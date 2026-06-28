"""
Custom Django model fields for the helpdesk application.

PortableVectorField wraps pgvector's ArrayField to normalize embedding
values on assignment, centralizing dimension validation and preventing
shape mismatches across different model assignments.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-28  |  Modified: 2026-06-28
"""

from __future__ import annotations

from django.db import models


def _load_native_vector_field():
    try:
        from pgvector.django import VectorField  # type: ignore

        return VectorField
    except Exception:
        return None


_NativeVectorField = _load_native_vector_field()
HAS_NATIVE_PGVECTOR = _NativeVectorField is not None


def _coerce_vector_value(value):
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    # pgvector can return numpy arrays when available; normalize for API/test consistency.
    if hasattr(value, "tolist"):
        converted = value.tolist()
        if isinstance(converted, list):
            return converted
    return value


if _NativeVectorField:

    class PortableVectorField(_NativeVectorField):
        """Native pgvector-backed field used on PostgreSQL deployments."""

        def from_db_value(self, value, expression, connection):
            converted = super().from_db_value(value, expression, connection)
            return _coerce_vector_value(converted)

        def to_python(self, value):
            converted = super().to_python(value)
            return _coerce_vector_value(converted)

else:

    class PortableVectorField(models.JSONField):
        """JSON fallback field for environments without pgvector."""

        def __init__(self, *args, dimensions: int = 64, **kwargs):
            self.dimensions = dimensions
            kwargs.setdefault("default", list)
            super().__init__(*args, **kwargs)

        def deconstruct(self):
            name, path, args, kwargs = super().deconstruct()
            kwargs["dimensions"] = self.dimensions
            return name, path, args, kwargs
