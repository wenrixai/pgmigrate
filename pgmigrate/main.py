import os
from pathlib import Path
from typing import Optional

import click
from attr import attrs, ib

from pgmigrate.db import DatabaseFacade, DatabaseMigrationError
from pgmigrate.files import load_migrations
from pgmigrate.logging import Logger
from pgmigrate.model import MigrationCollection, Migration, DatabaseStatus


def get_eligible_migrations(
    db_status: DatabaseStatus, spec: MigrationCollection, max_version: Optional[int] = None
) -> list[Migration]:
    result = []
    max_version = max_version or 2**32

    # Iterate migrations which are not executed, and find the next greatest one
    for migration in filter(
        lambda m: db_status.current_version is None or m.version > db_status.current_version, spec.migrations
    ):
        if migration.version > max_version:
            continue

        result.append(migration)

    return result


@attrs
class Context:
    logger: Logger = ib(default=None)
    migrations_spec = ib(default=None)
    database_status = ib(default=None)
    db_facade = ib(default=None)


@click.group()
@click.option("--path", type=click.Path(exists=True), required=True)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--verbose", "-v", is_flag=True, default=False)
@click.pass_context
def cli(ctx, verbose, path: Path, dry_run: bool):
    logger = Logger(verbose)
    db_facade = DatabaseFacade(os.environ["CONNECTION_STRING"], logger, dry_run=dry_run)
    db_facade.connect()
    database_status = db_facade.get_status()

    ctx.obj = Context(
        logger=logger, migrations_spec=load_migrations(Path(path)), db_facade=db_facade, database_status=database_status
    )


@cli.command()
@click.pass_context
@click.option("--version", type=int, required=False)
def migrate(ctx, version: Optional[int]):
    facade: DatabaseFacade = ctx.obj.db_facade

    eligible_migrations: list[Migration] = get_eligible_migrations(
        ctx.obj.database_status, ctx.obj.migrations_spec, max_version=version
    )

    if len(eligible_migrations) == 0:
        ctx.obj.logger.info("Database is up-to-date")
        return

    if ctx.obj.database_status.is_initialized is False:
        facade.initialize_db()

    for eligible_migration in eligible_migrations:
        try:
            facade.run_migration(eligible_migration)
        except DatabaseMigrationError as e:
            ctx.obj.logger.error(
                f"Error running migration {eligible_migration.name} ({eligible_migration.version}): {str(e)}"
            )

            raise

        ctx.obj.logger.success(f"Migration {eligible_migration.name} ({eligible_migration.version}) ran successfully")

    ctx.obj.logger.success("Finished executed all migrations successfully")


@cli.command()
@click.pass_context
def info(ctx):
    db_status: DatabaseStatus = ctx.obj.database_status

    if db_status.is_initialized is False:
        ctx.obj.logger.info("Database migration schema has not been initialized")
    else:
        eligible_migrations: list[Migration] = get_eligible_migrations(db_status, ctx.obj.migrations_spec)

        ctx.obj.logger.info(f"Database version is {db_status.current_version}")

        if len(eligible_migrations) == 0:
            ctx.obj.logger.info("Database is up-to-date")
        else:
            ctx.obj.logger.info(f"Need to apply versions {[x.version for x in eligible_migrations]}")


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
