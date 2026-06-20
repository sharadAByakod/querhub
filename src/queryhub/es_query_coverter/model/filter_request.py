from typing import Any, Optional, Union

from pydantic import BaseModel


class FilterRequest(BaseModel):
    field: str
    dsl: str
    value: Optional[Any] = None
    operation: str

    gte: Optional[Union[int, float]] = None
    gt: Optional[Union[int, float]] = None
    lte: Optional[Union[int, float]] = None
    lt: Optional[Union[int, float]] = None
