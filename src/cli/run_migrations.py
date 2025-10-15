from importlib import resources
from pathlib import Path

import click

from alembic import command
from alembic.config import Config
from src.config.config import ConfigModel, load_config


@click.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    default="configuration.toml",
    help="Path to a TOML config file (overrides default).",
)
def run_migrations(config: str):
    """
    Run alembic migrations on the database file, or create it if it does not already
    exist
    """
    config_dict: ConfigModel = load_config(Path(config))

    try:
        click.echo("Running database migrations with alembic...")

        with resources.path("src", "alembic.ini") as alembic_ini:
            alembic_cfg = Config(alembic_ini)

            alembic_cfg.set_main_option("sqlalchemy.url", config_dict.database.url)

            command.upgrade(alembic_cfg, "head")
    except Exception as e:
        click.echo(f"Error during database upgrade: {e}")
        raise click.Abort()


if __name__ == "__main__":
    run_migrations()
