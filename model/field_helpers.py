from typing import Any

from pydantic import Field


def WritableField(default: Any = None, **kwargs: Any):
    json_schema_extra = dict(kwargs.pop("json_schema_extra", {}) or {})
    json_schema_extra["writable"] = True
    return Field(default, json_schema_extra=json_schema_extra, **kwargs)
