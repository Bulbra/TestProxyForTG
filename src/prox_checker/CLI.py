import asyncio
import logging
import os
import time
from pprint import pp
import httpx
from dotenv import load_dotenv
from .main import run, load_proxies
from typing_extensions import Annotated
import typer

load_dotenv()
# https://api.telegram.org/bot{TOKEN}/getMe
TOKEN = os.getenv("BOT_TOKEN")
PROXY_LIST_URL = os.getenv("PROXY_LIST_URL")
app = typer.Typer()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@app.command()
def start(
        path: Annotated[str, typer.Argument(help="путь до файла с прокси")],
        timeout: Annotated[int, typer.Argument(help="таймаут запроса в секундах")] = 5,
        concurrency: Annotated[int, typer.Argument(help="количество одновременных проверок")] = 100,
        url: Annotated[str, typer.Argument(
            help="Сайт для которого вы ищете прокси")] = f"https://api.telegram.org/bot{TOKEN}/getMe",
):
    proxies = asyncio.run(load_proxies())

    logger.info(f"loaded: {len(proxies)}")

    res = asyncio.run(run(proxies, concurrency, timeout, url))

    with open(f"{path}", "w", encoding="utf-8") as f:
        for p, _ in res:
            f.write(p + "\n")
    logger.info(f"working: {len(res)}")


if __name__ == '__main__':
    app()
