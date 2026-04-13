# database/es_aggs.py

import logging
from typing import Any, Dict, Optional

from database.elasticsearch.elastic import get_es

logger = logging.getLogger(__name__)


def fetch_aggs(
    *,
    index: str,
    aggs: Dict[str, Any],
    query: Optional[Dict[str, Any]] = None,
) -> Any:

    es = get_es()

    body: Dict[str, Any] = {
        "size": 0,  # IMPORTANT
        "aggs": aggs,
    }

    if query:
        body["query"] = query

    resp = es.search(
        index=index,
        body=body,
    )

    return resp.get("aggregations", {})
