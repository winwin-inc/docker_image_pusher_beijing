"""WinWin Image Mirror - 主入口

提供命令行接口，将国外 Docker 镜像转存到阿里云私有仓库。
"""

import logging

import typer
from dotenv import load_dotenv

from .commands import list, push
from .commands.delete import register as delete_register
from .commands.sort import register as sort_register

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

app = typer.Typer()

list.register(app)
push.register(app)
delete_register(app)
sort_register(app)

if __name__ == "__main__":
    app()
