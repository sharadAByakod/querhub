from typing import Any, List

from fastapi import HTTPException

from es_query_coverter.filters.filter_builder import FilterNode
from es_query_coverter.filters.filter_group import FilterGroup
from es_query_coverter.model.filter_request import FilterRequest

RANGE_KEYS = {"gte", "gt", "lte", "lt"}
VALUE_DSL_MAP = {
    "eq": "eq",
    "is": "is",
    "in": "in",
    "one_of": "one_of",
    "wildcard": "wildcard",
    "regex": "regex",
    "match": "match",
    "match_phrase": "match_phrase",
    "phrase": "phrase",
    "prefix": "prefix",
    "contains": "contains",
    "starts_with": "starts_with",
    "ends_with": "ends_with",
}


def normalize_simple_query_params(data: Any) -> Any:
    if not isinstance(data, dict):
        return data

    normalized = dict(data)

    select = normalized.pop("select", None)
    if select is not None:
        source = dict(normalized.get("source") or {})
        source.setdefault("includes", select)
        normalized["source"] = source

    page = normalized.pop("page", None)
    size = normalized.pop("size", None)
    if page is not None or size is not None:
        pagination = dict(normalized.get("pagination") or {})
        if page is not None and "page" not in pagination:
            pagination["page"] = page
        if size is not None and "size" not in pagination:
            pagination["size"] = size
        normalized["pagination"] = pagination

    sort = normalized.get("sort")
    if sort is not None:
        normalized["sort"] = normalize_simple_sort(sort)

    where = normalized.pop("where", None)
    if where is not None:
        filters = list(normalized.get("filters") or [])
        filters.extend(parse_simple_where(where))
        normalized["filters"] = filters

    return normalized


def normalize_simple_sort(sort: Any) -> Any:
    if isinstance(sort, str):
        sort = [sort]

    if not isinstance(sort, list):
        return sort

    if not sort:
        return sort

    if all(isinstance(item, dict) for item in sort):
        return sort

    if not all(isinstance(item, str) for item in sort):
        raise HTTPException(
            status_code=400,
            detail="sort must be a list of strings or sort objects",
        )

    normalized = []
    for item in sort:
        order = "desc" if item.startswith("-") else "asc"
        field = item[1:] if item.startswith("-") else item
        normalized.append({"field": field, "order": order})

    return normalized


def parse_simple_where(where: Any) -> List[FilterNode]:
    if where is None:
        return []

    if isinstance(where, list):
        conditions = [_parse_condition(item, attach_operation="AND") for item in where]
        return [FilterGroup(operation="AND", conditions=conditions)]

    return [_parse_condition(where, attach_operation="AND")]


def _parse_condition(condition: Any, attach_operation: str) -> FilterNode:
    if not isinstance(condition, dict) or not condition:
        raise HTTPException(
            status_code=400,
            detail="where conditions must be non-empty objects",
        )

    conditions: List[FilterNode] = []

    for key, value in condition.items():
        if key == "all":
            for item in _ensure_list(value, key):
                conditions.append(_parse_condition(item, attach_operation="AND"))
            continue

        if key == "any":
            any_conditions = [
                _parse_condition(item, attach_operation="OR")
                for item in _ensure_list(value, key)
            ]
            conditions.append(FilterGroup(operation="AND", conditions=any_conditions))
            continue

        if key == "not":
            for item in _ensure_list(value, key):
                conditions.append(_parse_condition(item, attach_operation="NOT"))
            continue

        conditions.extend(_parse_field_condition(key, value))

    if not conditions:
        raise HTTPException(
            status_code=400,
            detail="where conditions must contain at least one supported operator",
        )

    if len(conditions) == 1:
        return _reattach_single_condition(conditions[0], attach_operation)

    return FilterGroup(operation=attach_operation, conditions=conditions)


def _parse_field_condition(field: str, value: Any) -> List[FilterRequest]:
    if isinstance(value, list):
        return [
            FilterRequest(field=field, dsl="in", value=value, operation="AND"),
        ]

    if not isinstance(value, dict):
        return [
            FilterRequest(field=field, dsl="eq", value=value, operation="AND"),
        ]

    if not value:
        raise HTTPException(
            status_code=400,
            detail=f"Field '{field}' must not use an empty operator object",
        )

    conditions: List[FilterRequest] = []
    range_kwargs = _extract_range_kwargs(field, value)

    if range_kwargs:
        conditions.append(
            FilterRequest(field=field, dsl="range", operation="AND", **range_kwargs)
        )

    for operator, operator_value in value.items():
        if operator in RANGE_KEYS or operator == "range":
            continue

        if operator in ("neq", "not_eq"):
            conditions.append(
                FilterRequest(field=field, dsl="eq", value=operator_value, operation="NOT")
            )
            continue

        if operator == "not_in":
            conditions.append(
                FilterRequest(field=field, dsl="in", value=operator_value, operation="NOT")
            )
            continue

        if operator == "exists":
            if not isinstance(operator_value, bool):
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field}' exists operator must be boolean",
                )

            operation = "AND" if operator_value else "NOT"
            conditions.append(
                FilterRequest(field=field, dsl="exists", value=True, operation=operation)
            )
            continue

        mapped_dsl = VALUE_DSL_MAP.get(operator)
        if mapped_dsl is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported operator '{operator}' for field '{field}'",
            )

        conditions.append(
            FilterRequest(
                field=field,
                dsl=mapped_dsl,
                value=operator_value,
                operation="AND",
            )
        )

    if not conditions:
        raise HTTPException(
            status_code=400,
            detail=f"Field '{field}' must contain a supported operator",
        )

    return conditions


def _extract_range_kwargs(field: str, value: dict[str, Any]) -> dict[str, Any]:
    range_kwargs = {key: value[key] for key in RANGE_KEYS if key in value}

    range_value = value.get("range")
    if range_value is not None:
        if not isinstance(range_value, dict):
            raise HTTPException(
                status_code=400,
                detail=f"Field '{field}' range operator must be an object",
            )

        for key, item in range_value.items():
            if key not in RANGE_KEYS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported range key '{key}' for field '{field}'",
                )
            range_kwargs[key] = item

    return range_kwargs


def _ensure_list(value: Any, key: str) -> list[Any]:
    if isinstance(value, list) and value:
        return value

    raise HTTPException(
        status_code=400,
        detail=f"'{key}' must be a non-empty list",
    )


def _reattach_single_condition(condition: FilterNode, operation: str) -> FilterNode:
    if isinstance(condition, FilterRequest):
        if condition.operation == "AND":
            return condition.model_copy(update={"operation": operation})
        if operation == "AND":
            return condition
        if condition.operation == operation:
            return condition

        return FilterGroup(operation=operation, conditions=[condition])

    return condition.model_copy(update={"operation": operation})
