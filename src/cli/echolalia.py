"""
This is the top-most command
"""

from pathlib import Path

import click
from click import Context

from src.cli.run_daemon import run_daemon
from src.cli.run_migrations import run_migrations


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    default="configuration.toml",
    help="Path to a TOML config file (overrides default).",
)
@click.pass_context
def echolalia(ctx: Context, config: Path):
    """
    Analysis daemon - manage and run analysis tasks
    """
    ctx.ensure_object(dict)
    ctx.obj["config"] = config


echolalia.add_command(run_daemon)
echolalia.add_command(run_migrations)

if __name__ == "__main__":
    echolalia()
