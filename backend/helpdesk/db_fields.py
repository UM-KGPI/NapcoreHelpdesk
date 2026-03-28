from __future__ import annotations

from django.conf import settings
from django.db import models


def _is_sqlite_default_engine() -> bool:
    engine = settings.DATABASES.get("default", {}).get("ENGINE", "")
    return engine.endswith("sqlite3")


def _load_native_vector_field():
    if _is_sqlite_default_engine():
        return None
    try:
        from pgvector.django import VectorField  # type: ignore

        return VectorField
    except Exception:
        return None


_NativeVectorField = _load_native_vector_field()
HAS_NATIVE_PGVECTOR = _NativeVectorField is not None


if _NativeVectorField:

    class PortableVectorField(_NativeVectorField):
        """Native pgvector-backed field used on PostgreSQL deployments."""

        pass

else:

    class PortableVectorField(models.JSONField):
        """JSON fallback field for SQLite/local test compatibility."""

        def __init__(self, *args, dimensions: int = 64, **kwargs):
            self.dimensions = dimensions
            kwargs.setdefault("default", list)
            super().__init__(*args, **kwargs)

        def deconstruct(self):
            name, path, args, kwargs = super().deconstruct()
            kwargs["dimensions"] = self.dimensions
            return name, path, args, kwargs
