import glob
from pathlib import Path

import yaml

from src.pgmigrate.model import Migration, MigrationCollection, MigrationSchemaValidator

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader as Loader


def load_migrations(path: Path) -> MigrationCollection:
    migrations = []

    for file in glob.glob(str(path / "**/*.yml"), recursive=True):
        loaded = yaml.load(open(file, "r"), Loader=Loader)
        MigrationSchemaValidator.validate(loaded)

        migrations.append(Migration(**loaded))

    return MigrationCollection(migrations)
