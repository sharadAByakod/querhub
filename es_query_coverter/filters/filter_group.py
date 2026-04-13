from typing import List, Literal, Union

from pydantic import BaseModel

from es_query_coverter.model.filter_request import FilterRequest


class FilterGroup(BaseModel):
    operation: Literal["AND", "OR", "NOT"] = "AND"
    conditions: List[Union["FilterGroup", FilterRequest]]  # recursive


# Fix forward references
FilterGroup.model_rebuild()
