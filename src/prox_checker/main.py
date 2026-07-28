import asyncio
import logging
import os
import time
from pprint import  pp
import httpx
from dotenv import load_dotenv

from typing_extensions import Annotated
import typer

load_dotenv()
# https://api.telegram.org/bot{TOKEN}/getMe
TOKEN = os.getenv("BOT_TOKEN")
my_url = f"https://api.telegram.org/bot{TOKEN}/getMe"
my_concurrency = 100
my_timeout = 5
PROXY_LIST_URL = os.getenv("PROXY_LIST_URL")

app = typer.Typer()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)




logger = logging.getLogger(__name__)


async def load_proxies() -> list[str]:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(PROXY_LIST_URL)
        r.raise_for_status()
        data = r.json()

    proxies = []

    for prox in data:
        p = prox["proxy"].strip()

        if not p or p.startswith("#"):
            continue

        if not p.startswith("http"):
            p = "http://" + p

        proxies.append(p)
    pp(proxies)
    return proxies


def make_client(proxy, timeout):
    return httpx.AsyncClient(
        proxy=proxy,
        timeout=timeout,
        verify=False,
    )


async def check(proxy: str, idx: int, timeout: int, url:str):
    started = time.perf_counter()

    try:
        async with make_client(proxy, timeout) as client:
            response = await client.get(url)

        if response.status_code != 200:
            return

        if not response.json().get("ok"):
            return

        elapsed = time.perf_counter() - started

        logger.info(f"[{idx}] {proxy} {elapsed:.2f}s")

        return proxy, elapsed

    except (
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.ProxyError,
            httpx.ConnectError,
    ):
        return

    except Exception as exc:
        logger.error(f"[{idx}] {exc}")
        return


async def run(proxies: list[str], concurrency, timeout, url):
    sem = asyncio.Semaphore(concurrency)

    total = len(proxies)
    done = 0
    ok = []

    t0 = time.perf_counter()

    async def worker(i, p):
        async with sem:
            return await check(p, i, timeout, url)

    tasks = [
        asyncio.create_task(worker(i, p))
        for i, p in enumerate(proxies, 1)
    ]

    for t in asyncio.as_completed(tasks):
        res = await t

        done += 1

        if res:
            ok.append(res)
        if done % 20 == 0 or done == total:
            dt = time.perf_counter() - t0
            speed = done / dt if dt else 0

            logger.info(f"[progress] {done}/{total} {done / total * 100:.1f}% ok={len(ok)} {speed:.1f}/sec")

    return ok



if __name__ == '__main__':
    proxies = asyncio.run(load_proxies())

    logger.info(f"loaded: {len(proxies)}")
    res = asyncio.run(run(proxies, my_concurrency, my_timeout, my_url))


    with open("../../working_proxies.txt", "w", encoding="utf-8") as f:
        for p, _ in res:
            f.write(p + "\n")
    logger.info(f"working: {len(res)}")