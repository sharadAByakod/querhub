from typing import List, Optional, Union

from pydantic import BaseModel, Field, model_validator

from es_query_coverter.filters.filter_group import FilterGroup
from es_query_coverter.model.es_sort import SortRequest
from es_query_coverter.model.filter_request import FilterRequest
from es_query_coverter.model.pagination import PaginationRequest
from es_query_coverter.model.source_filter import SourceFilter
from es_query_coverter.utils.simple_query_parser import normalize_simple_query_params


class QueryParams(BaseModel):
    sort: Optional[List[SortRequest]] = None
    pagination: PaginationRequest = Field(default_factory=PaginationRequest)
    source: Optional[SourceFilter] = None
    filters: Optional[List[Union[FilterRequest, FilterGroup]]] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_simple_inputs(cls, value):
        return normalize_simple_query_params(value)
