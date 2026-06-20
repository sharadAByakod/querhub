from pydantic import BaseModel, Field
from typing import Literal


class SortRequest(BaseModel):
    field: str = Field(..., description="Field name to sort by")
    order: Literal["asc", "desc"] = Field(..., description="Sort direction")
