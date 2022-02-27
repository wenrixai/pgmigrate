import psycopg2
from psycopg2.extras import DictCursor

from pgmigrate.logging import Logger
from pgmigrate.model import Migration, SchemaHistory

VERSION_TABLE_NAME = "schema_history"


class DatabaseMigrationError(Exception):
    pass


class ValidationFailed(DatabaseMigrationError):
    def __init__(self, validation: str):
        pass


def is_table_exists(cursor) -> bool:
    cursor.execute(
        "select exists(select * from information_schema.tables where table_name=%s) as has_table",
        (VERSION_TABLE_NAME,),
    )
    return cursor.fetchone()["has_table"]


class DatabaseFacade:
    def __init__(self, connection_string: str, logger: Logger, dry_run: bool = False) -> None:
        self._connection_string = connection_string
        self._logger = logger
        self._dry_run = dry_run

        self.versions: list[SchemaHistory] = None
        self.is_started = False
        self._connection = None

    @property
    def current_version(self) -> int:
        return None if self.versions is None else max([h.version for h in self.versions])

    def initialize_db(self):
        """
        Setup initial DB migration table
        """
        with self._connection.cursor() as cursor:
            cursor.execute(
                "CREATE TABLE {} (id integer, timestamp timestamp with out timezone;".format(VERSION_TABLE_NAME)
            )

        self._logger.debug(f"Created table {VERSION_TABLE_NAME} successfully")

    def _load_versions(self):
        with self._connection.cursor() as cursor:
            self.is_started = is_table_exists(cursor)

            if self.is_started:
                self.versions = [
                    SchemaHistory(**x)
                    for x in cursor.fetch("SELECT version, timestamp FROM {};".format(VERSION_TABLE_NAME))
                ]

    def connect(self) -> None:
        self._connection = psycopg2.connect(dsn=self._connection_string, cursor_factory=DictCursor)

        self._logger.debug("Connected to DB successfully")
        self._load_versions()

    def run_migration(self, migration_file: Migration) -> None:
        with self._connection.cursor() as cursor:
            try:
                for statement in migration_file.migration:
                    cursor.execute(statement)
                    self._logger.debug(f"Executed {statement} successfully")

                # TODO: Verify if exists

                cursor.execute(
                    "INSERT INTO {} VALUES(%s, CURRENT_TIMESTAMP);".format(VERSION_TABLE_NAME),
                    (migration_file.id,),
                )

                if self._dry_run:
                    self._connection.rollback()
                    self._logger.debug("Dry run mode, rolling back")
                else:
                    self._connection.commit()
                    self._logger.debug(f"Commiting transaction {migration_file.id}")
            except Exception:
                self._connection.rollback()
                raise
