from importlib import resources
from pathlib import Path

import click
from click import Context

from alembic import command
from alembic.config import Config
from src.config.config import ConfigModel, load_config
from src.service_layer.bootstrap import setup_logging


@click.command()
@click.pass_context
def run_migrations(ctx: Context):
    """
    Run alembic migrations on the database file, or create it if it does not already
    exist
    """
    config: str = ctx.obj["config"]
    config_model: ConfigModel = load_config(Path(config))
    logger = setup_logging(config_model)

    try:
        logger.info("Running database migrations with alembic...")

        with resources.path("src", "alembic.ini") as alembic_ini:
            alembic_cfg = Config(alembic_ini)

            alembic_cfg.set_main_option("sqlalchemy.url", config_model.database.url)

            command.upgrade(alembic_cfg, "head")
    except Exception as e:
        logger.exception(f"Error during database upgrade: {e}")
        raise click.Abort()
