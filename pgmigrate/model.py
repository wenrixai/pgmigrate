from datetime import datetime
from typing import Optional

from attr import attrs, ib
from jsonschema.validators import Draft4Validator


@attrs
class Migration:
    id: int = ib()
    name: str = ib()
    description: str = ib()
    migration: str = ib()
    verify: Optional[str] = ib()
    undo: str = ib()


@attrs
class SchemaHistory:
    version: int = ib()
    timestamp: datetime = ib()


MigrationSchemaValidator = Draft4Validator(
    {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "properties": {
            "id": {"type": "integer", "minimum": 0},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "migration": {"type": "array", "items": [{"type": "string"}], "minItems": 1, "uniqueItems": True},
            "verify": {"type": "array", "items": [{"type": "string"}], "minItems": 1, "uniqueItems": True},
            "undo": {"type": "array", "items": [{"type": "string"}], "minItems": 1, "uniqueItems": True},
        },
        "required": ["id", "name", "description", "migration"],
    }
)


@attrs
class MigrationCollection:
    migrations: list[Migration] = ib()

    def __attrs_post_init__(self):
        ids = [x.id for x in self.migrations]

        if len(ids) != len(set(ids)):
            raise ValueError("Some migrations IDs defined more than once")

        # Sorting is important later on
        self.migrations = sorted(self.migrations, key=lambda x: x.id)

    @property
    def last_version(self) -> int:
        return max([mf.id for mf in self.migrations], default=None)
