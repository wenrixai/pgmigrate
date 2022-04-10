from datetime import datetime
from typing import Optional

from attr import attrs, ib
from jsonschema.validators import Draft4Validator


@attrs
class Migration:
    version: int = ib()
    name: str = ib()
    description: str = ib()
    migration: str = ib()
    verify: Optional[list[str]] = ib(factory=list)
    undo: Optional[list[str]] = ib(factory=list)


@attrs
class SchemaHistory:
    version: int = ib()
    timestamp: datetime = ib()


MigrationSchemaValidator = Draft4Validator(
    {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "properties": {
            "version": {"type": "integer", "minimum": 0},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "migration": {"type": "array", "items": [{"type": "string"}], "minItems": 1},
            "verify": {"type": "array", "items": [{"type": "string"}], "minItems": 1},
            "undo": {"type": "array", "items": [{"type": "string"}], "minItems": 1},
        },
        "required": ["version", "name", "description", "migration"],
    }
)


@attrs
class MigrationCollection:
    migrations: list[Migration] = ib()

    def __attrs_post_init__(self):
        ids = [x.version for x in self.migrations]

        if len(ids) != len(set(ids)):
            raise ValueError("Some migrations IDs defined more than once")

        # Sorting is important later on
        self.migrations = sorted(self.migrations, key=lambda x: x.version)


@attrs
class DatabaseStatus:
    is_initialized: bool = ib()
    history: list[SchemaHistory] = ib()

    @property
    def current_version(self) -> int:
        return max((x.version for x in self.history), default=None)
