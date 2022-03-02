import click


class Logger:
    def __init__(self, is_verbose: bool) -> None:
        self._is_verbose = is_verbose

    def error(self, message: str) -> None:
        click.echo(click.style(message, fg="red"))

    def success(self, message: str) -> None:
        click.echo(click.style(message, fg="green"))

    def info(self, message: str) -> None:
        click.echo(click.style(message))

    def debug(self, message: str) -> None:
        if self._is_verbose:
            click.echo(click.style(message))
