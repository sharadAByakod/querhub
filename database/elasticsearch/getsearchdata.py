# database/es_pit.py

import logging
from typing import Any, Dict, Iterator, List, Optional

from database.elasticsearch.elastic import get_es

logger = logging.getLogger(__name__)

PIT_KEEP_ALIVE = "1m"
DEFAULT_BATCH_SIZE = 1000


def fetch_page(
    *,
    index: str,
    query: Optional[Dict[str, Any]] = None,
    sort: Optional[List[Dict[str, Any]]] = None,
    source: Optional[Dict[str, Any]] = None,
    size: int = 100,
    offset: int = 0,
) -> tuple[List[Dict[str, Any]], int]:
    """
    Fetch a single page of results using standard from/size pagination.
    """

    es = get_es()

    body: Dict[str, Any] = {
        "from": offset,
        "size": size,
        "sort": sort or [{"_shard_doc": "asc"}],
        "track_total_hits": True,
    }

    if query:
        body["query"] = query

    if source:
        body.update(source)

    resp = es.search(index=index, body=body)
    total = resp["hits"]["total"]

    if isinstance(total, dict):
        total = total.get("value", 0)

    return resp["hits"]["hits"], int(total)


def fetch_all_with_pit(
    *,
    index: str,
    query: Optional[Dict[str, Any]] = None,
    sort: Optional[List[Dict[str, Any]]] = None,
    source: Optional[Dict[str, Any]] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> List[Dict[str, Any]]:
    """
    Fetch ALL matched documents using PIT + search_after.

    ⚠ WARNING:
    - Loads all docs into memory.
    - Use only for internal jobs or bounded datasets.
    """

    es = get_es()
    pit_id: Optional[str] = None
    all_hits: List[Dict[str, Any]] = []

    try:
        pit_id = es.open_point_in_time(
            index=index,
            keep_alive=PIT_KEEP_ALIVE,
        )["id"]

        body: Dict[str, Any] = {
            "size": batch_size,
            "pit": {
                "id": pit_id,
                "keep_alive": PIT_KEEP_ALIVE,
            },
            "sort": sort or [{"_shard_doc": "asc"}],
        }

        if query:
            body["query"] = query

        if source:
            body.update(source)

        while True:
            resp = es.search(body=body)
            hits = resp["hits"]["hits"]

            if not hits:
                break

            all_hits.extend(hits)
            body["search_after"] = hits[-1]["sort"]

        return all_hits

    finally:
        if pit_id:
            try:
                es.close_point_in_time(body={"id": pit_id})
            except Exception as exc:
                logger.warning("Failed to close PIT %s: %r", pit_id, exc)


def iter_all_with_pit(
    *,
    index: str,
    query: Optional[Dict[str, Any]] = None,
    sort: Optional[List[Dict[str, Any]]] = None,
    source: Optional[Dict[str, Any]] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> Iterator[Dict[str, Any]]:
    """
    Stream ALL matched documents using PIT + search_after.
    Safe for millions of docs.
    """

    es = get_es()
    pit_id: Optional[str] = None

    try:
        pit_id = es.open_point_in_time(
            index=index,
            keep_alive=PIT_KEEP_ALIVE,
        )["id"]

        body: Dict[str, Any] = {
            "size": batch_size,
            "pit": {
                "id": pit_id,
                "keep_alive": PIT_KEEP_ALIVE,
            },
            "sort": sort or [{"_shard_doc": "asc"}],
        }

        if query:
            body["query"] = query

        if source:
            body.update(source)

        while True:
            resp = es.search(body=body)
            hits = resp["hits"]["hits"]

            if not hits:
                break

            for hit in hits:
                yield hit

            body["search_after"] = hits[-1]["sort"]

    finally:
        if pit_id:
            try:
                es.close_point_in_time(body={"id": pit_id})
            except Exception as exc:
                logger.warning("Failed to close PIT %s: %r", pit_id, exc)
