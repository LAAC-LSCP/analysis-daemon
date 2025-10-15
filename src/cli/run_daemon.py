"""
The run-daemon command is the entry-point for our daemon in a production environment
"""

import asyncio
from pathlib import Path

import click

from src.service_layer.bootstrap import bootstrap


@click.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    default="configuration.toml",
    help="Path to a TOML config file (overrides default).",
)
def run_daemon(config: str) -> None:
    service = bootstrap(Path(config))
    asyncio.run(service.main_loop())


# For the purpose of debugging
if __name__ == "__main__":
    run_daemon()
