from importlib import resources

import click

from alembic import command
from alembic.config import Config


@click.command()
def run_migrations():
    """
    Run alembic migrations on the database file, or create it if it does not already
    exist
    """
    try:
        click.echo("Running database migrations with alembic...")

        with resources.path("src", "alembic.ini") as alembic_ini:
            alembic_cfg = Config(alembic_ini)
            command.upgrade(alembic_cfg, "head")
    except Exception as e:
        click.echo(f"Error during database upgrade: {e}")
        raise click.Abort()


if __name__ == "__main__":
    run_migrations()
