from typing import Any, List, Optional, Union

from pydantic import BaseModel, field_validator


class SourceFilter(BaseModel):
    includes: Optional[Union[str, List[str]]] = None
    excludes: Optional[Union[str, List[str]]] = None

    @field_validator("includes", "excludes", mode="before")
    @classmethod
    def normalize_source_fields(cls, v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        raise ValueError("includes/excludes must be a string or list of strings")  # noqa
