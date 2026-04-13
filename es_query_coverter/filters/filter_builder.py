from typing import Any, Dict, List, Union

from fastapi import HTTPException

from es_query_coverter.filters.dsl_factory import DSLFactory
from es_query_coverter.filters.filter_group import FilterGroup
from es_query_coverter.model.filter_request import FilterRequest
from es_query_coverter.utils.query_builder_helpers import QueryBuilderHelpers

FilterNode = Union[FilterRequest, FilterGroup]


class FilterBuilder:

    def __init__(self, model_fields: List[str]):
        self.model_fields = model_fields

    # -----------------------------------------------------
    # PUBLIC ENTRY
    # -----------------------------------------------------
    def build(self, filters: List[FilterNode]) -> Dict[str, Any]:
        if not filters:
            return {}

        root_bool = self._parse_group(filters)
        return self._prune(root_bool)

    # -----------------------------------------------------
    # RECURSIVE GROUP PARSER
    # -----------------------------------------------------
    def _parse_group(self, nodes: List[FilterNode]) -> Dict[str, Any]:

        bool_query: Dict[str, Dict[str, List[Any]]] = {
            "bool": {"must": [], "should": [], "must_not": []}
        }

        for node in nodes:

            # --------------------------------------------
            # Nested FilterGroup
            # --------------------------------------------
            if isinstance(node, FilterGroup):
                nested = self._parse_group(node.conditions)
                self._append_by_operation(bool_query["bool"], node.operation, nested)
                continue

            # --------------------------------------------
            # Leaf FilterRequest
            # --------------------------------------------
            if isinstance(node, FilterRequest):

                # FIELD VALIDATION
                QueryBuilderHelpers.validate_field_name(
                    node.field, self.model_fields, "filter"
                )

                # Custom rule: wildcard not allowed for range
                if node.dsl == "range" and "*" in node.field:
                    raise HTTPException(400, "Wildcard is not allowed for range DSL")

                # -----------------------------------------------------
                # BUILD DSL CLAUSE
                # -----------------------------------------------------

                # RANGE DSL → uses gte/gt/lte/lt only
                if node.dsl == "range":
                    clause = DSLFactory.build_clause(
                        dsl=node.dsl,
                        field=node.field,
                        gte=node.gte,
                        gt=node.gt,
                        lte=node.lte,
                        lt=node.lt,
                    )

                # ALL OTHER DSLs → use value
                else:
                    clause = DSLFactory.build_clause(
                        dsl=node.dsl,
                        field=node.field,
                        value=node.value,
                    )

                # -----------------------------------------------------
                # BOOLEAN LOGIC HANDLING
                # -----------------------------------------------------
                self._append_by_operation(bool_query["bool"], node.operation, clause)

        return bool_query

    # -----------------------------------------------------
    # Only append non-empty entries
    # -----------------------------------------------------
    def _append(self, target: Dict[str, Any], key: str, value: Any):
        if value and value not in ({}, []):
            target[key].append(value)

    def _append_by_operation(
        self, target: Dict[str, Any], operation: str, value: Any
    ) -> None:
        operation_map = {
            "AND": "must",
            "OR": "should",
            "NOT": "must_not",
        }

        key = operation_map.get(operation)
        if key is None:
            raise HTTPException(400, f"Invalid boolean operator: {operation}")

        self._append(target, key, value)

    # -----------------------------------------------------
    # Recursively prune empty lists or dicts
    # -----------------------------------------------------
    def _prune(self, node: Any):
        if isinstance(node, dict):
            cleaned = {}
            for k, v in node.items():
                val = self._prune(v)
                if val not in (None, [], {}):
                    cleaned[k] = val
            return cleaned

        if isinstance(node, list):
            cleaned_list = [self._prune(v) for v in node]
            cleaned_list = [c for c in cleaned_list if c not in (None, [], {})]
            return cleaned_list

        return node
