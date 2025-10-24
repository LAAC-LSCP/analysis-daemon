"""
The run-daemon command is the entry-point for our daemon in a production environment
"""

import asyncio
from pathlib import Path

import click
from click import Context

from src.service_layer.bootstrap import bootstrap


@click.command()
@click.pass_context
def run_daemon(ctx: Context) -> None:
    config: str = ctx.obj["config"]

    service = bootstrap(Path(config))
    asyncio.run(service.main_loop())
