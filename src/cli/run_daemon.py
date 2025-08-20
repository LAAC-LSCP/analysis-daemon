import click


@click.command()
def run_daemon() -> None:
    raise NotImplementedError


# For the purpose of debugging
if __name__ == "__main__":
    run_daemon()
