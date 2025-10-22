"""
This is the top-most command
"""

import click

from src.cli.run_daemon import run_daemon
from src.cli.run_migrations import run_migrations


@click.group()
def echolalia():
    """
    Analysis daemon - manage and run analysis tasks
    """
    pass


echolalia.add_command(run_daemon)
echolalia.add_command(run_migrations)

if __name__ == "__main__":
    echolalia()
