from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

# Filter imports (modular)
from es_query_coverter.filters.filter_builder import FilterBuilder
from es_query_coverter.filters.filter_group import FilterGroup
from es_query_coverter.model.es_sort import SortRequest
from es_query_coverter.model.filter_request import FilterRequest
from es_query_coverter.model.pagination import PaginationRequest
from es_query_coverter.model.source_filter import SourceFilter
from es_query_coverter.utils.query_builder_helpers import QueryBuilderHelpers


class ESQueryBuilder:
    """
    Core ES builder supporting:
        - Sorting
        - Pagination
        - _source includes/excludes
        - Filters (via FilterBuilder)
    """

    def __init__(self, model: Type[BaseModel]):
        self.model = model
        self.model_fields = QueryBuilderHelpers.collect_model_fields(model)

    # -------------------------------------------------------
    # FILTERS (delegated to FilterBuilder)
    # -------------------------------------------------------
    def build_filters(
        self, filters: Optional[List[FilterRequest | FilterGroup]]
    ) -> Dict[str, Any]:

        if not filters:
            return {}

        filter_builder = FilterBuilder(self.model_fields)
        result = filter_builder.build(filters)

        return result  # already pruned and clean {"bool": {...}}

    # -------------------------------------------------------
    # SORTING
    # -------------------------------------------------------
    def build_sort(
        self, sort_items: Optional[List[SortRequest]]
    ) -> List[Dict[str, Any]]:

        if not sort_items:
            return []

        result: List[Dict[str, Any]] = []
        special_sort_fields = {"_score", "_shard_doc", "_doc", "_id"}

        for item in sort_items:
            if item.field not in special_sort_fields:
                QueryBuilderHelpers.validate_field_name(
                    item.field, self.model_fields, "sort"
                )
            result.append({item.field: {"order": item.order}})

        return result

    # -------------------------------------------------------
    # PAGINATION
    # -------------------------------------------------------
    def build_pagination(self, pagination: Optional[PaginationRequest]):
        """
        Returns (size, from)
        """

        if not pagination:
            return 100, 0

        size = pagination.size or 100
        page = pagination.page or 0

        return size, size * page

    # -------------------------------------------------------
    # _SOURCE INCLUDES/EXCLUDES
    # -------------------------------------------------------
    def build_source(self, source: Optional[SourceFilter]) -> Dict[str, Any]:

        if not source:
            return {}

        includes_list = QueryBuilderHelpers.ensure_list(source.includes)
        excludes_list = QueryBuilderHelpers.ensure_list(source.excludes)

        # Validate includes
        if includes_list:
            for f in includes_list:
                QueryBuilderHelpers.validate_field_name(
                    f, self.model_fields, "includes"
                )

        # Validate excludes
        if excludes_list:
            for f in excludes_list:
                QueryBuilderHelpers.validate_field_name(
                    f, self.model_fields, "excludes"
                )

        # Nothing to return
        if not includes_list and not excludes_list:
            return {}

        _source: Dict[str, Any] = {}

        if includes_list:
            _source["includes"] = includes_list
        if excludes_list:
            _source["excludes"] = excludes_list

        return {"_source": _source}
