from src.bootstrap.bootstrap import bootstrap

from pathlib import Path
import click


@click.command()
@click.option(
    "--config", "-c",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    default='configuration.toml',
    help="Path to a TOML config file (overrides default)."
)
def run_daemon(config) -> None:
    service = bootstrap(Path(config))
    service.main_loop()


# For the purpose of debugging
if __name__ == "__main__":
    run_daemon()
