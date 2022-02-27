from pathlib import Path
from typing import Optional

import click
from attr import attrs, ib

from pgmigrate.db import DatabaseFacade, DatabaseMigrationError
from pgmigrate.files import load_migrations
from pgmigrate.logging import Logger
from pgmigrate.model import MigrationCollection, Migration


def get_eligible_migrations(
    versions: list, spec: MigrationCollection, max_version: Optional[int] = None
) -> list[Migration]:
    result = []
    last = max(x.id for x in versions)
    max_version = max_version or 2**32

    # Iterate migrations which are not executed, and find the next greatest one
    for migration in filter(lambda m: m.id > last, spec.migrations):
        if migration.id > max_version:
            break

        result.append(migration)

    return result


@attrs
class Context:
    logger: Logger = ib()
    migrations_spec = ib(default=None)
    db_facade = ib(default=None)


@click.group()
@click.option(
    "--connection-string",
    envvar="PGMIGRATE_CONNECTION_STRING",
    hide_input=True,
    required=True,
)
@click.option("--path", type=click.Path(exists=True), required=True)
@click.option("--dry-run", type=bool, default=False)
@click.option("--verbose", default=False)
@click.pass_context
def cli(ctx, verbose, path: Path, connection_string: str, dry_run: bool):
    logger = Logger(verbose)

    ctx.obj.logger = logger
    ctx.obj.migrations_spec = load_migrations(Path(path))
    ctx.obj.db_facade = DatabaseFacade(connection_string, logger, dry_run=dry_run)


@cli.command()
@click.pass_context
@click.option("--version", type=int, required=False)
def migrate(ctx, version: Optional[int]):
    facade: DatabaseFacade = ctx.obj.db_facade
    facade.connect()

    eligible_migrations: list[Migration] = get_eligible_migrations(
        facade.versions, ctx.obj.migrations_spec, max_version=version
    )

    if len(eligible_migrations) == 0:
        ctx.obj.logger.info("Database is up-to-date")
        return

    with click.progressbar(eligible_migrations) as bar:
        for eligible_migration in bar:
            try:
                facade.run_migration(eligible_migration)
            except DatabaseMigrationError as e:
                ctx.obj.logger.error(
                    f"Error running migration {eligible_migration.name} ({eligible_migration.id}): {str(e)}"
                )

                raise

            ctx.obj.logger.success(f"Migration {eligible_migration.name} ({eligible_migration.id}) ran successfully")

    ctx.obj.logger.success("Finished executed all migrations successfully")


@cli.command()
@click.pass_context
def info(ctx):
    facade: DatabaseFacade = ctx.obj.db_facade
    facade.connect()

    current_version = facade.current_version
    if current_version is None:
        ctx.obj.logger.info("Database migration schema has not been initialized")
    else:
        eligible_migrations: list[Migration] = get_eligible_migrations(facade.versions, ctx.obj.migrations_spec)

        ctx.obj.logger.info(f"Database version is {current_version}")
        ctx.obj.logger.info(f"Need to apply versions {[x.id for x in eligible_migrations]}")


@cli.command()
@click.pass_context
def clean(ctx):
    raise NotImplementedError()


@cli.command()
@click.option("--version", type=int)
@click.pass_context
def undo(ctx):
    raise NotImplementedError()


if __name__ == "__main__":
    cli.add_command(migrate)
    cli(obj=Context)
