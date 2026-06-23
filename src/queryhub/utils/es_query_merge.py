from typing import Any


def merge_view_query(
    *,
    request_query: dict[str, Any] | None,
    base_query: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """
    Merge a client-supplied query with a view-level Elasticsearch query.

    The incoming request query stays in `must` so text queries can still score.
    The fixed view query is applied in `filter` so it always constrains results.
    """

    if not request_query:
        return base_query

    if not base_query:
        return request_query

    return {
        "bool": {
            "must": [request_query],
            "filter": [base_query],
        }
    }
