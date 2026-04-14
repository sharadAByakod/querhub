from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from database.elasticsearch.elastic import get_es


def _extract_error_status(exc: Exception) -> int:
    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int):
        return status_code

    meta = getattr(exc, "meta", None)
    meta_status = getattr(meta, "status", None)
    if isinstance(meta_status, int):
        return meta_status

    return 500


def _extract_error_body(exc: Exception) -> Any:
    body = getattr(exc, "body", None)
    if body is not None:
        return body

    return {
        "type": exc.__class__.__name__,
        "reason": str(exc),
    }


def _raise_write_error(
    *,
    message: str,
    failures: List[Dict[str, Any]],
    status_code: int = 500,
) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={
            "message": message,
            "failures": failures,
        },
    )


def write_document(
    *,
    index: str,
    document: Dict[str, Any],
    document_id: Optional[str] = None,
    upsert: bool = True,
) -> Dict[str, Any]:
    es = get_es()

    try:
        if document_id:
            response = es.update(
                index=index,
                id=document_id,
                doc=document,
                doc_as_upsert=upsert,
                refresh="wait_for",
            )
            return {
                "id": response["_id"],
                "result": response.get("result", "updated"),
            }

        response = es.index(
            index=index,
            document=document,
            refresh="wait_for",
        )
        return {
            "id": response["_id"],
            "result": response.get("result", "created"),
        }
    except HTTPException:
        raise
    except Exception as exc:
        _raise_write_error(
            message="Write request failed",
            status_code=_extract_error_status(exc),
            failures=[
                {
                    "id": document_id,
                    "status": _extract_error_status(exc),
                    "error": _extract_error_body(exc),
                }
            ],
        )


def write_documents(
    *,
    index: str,
    updates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    es = get_es()

    operations: List[Dict[str, Any]] = []
    for item in updates:
        operations.append(
            {
                "update": {
                    "_index": index,
                    "_id": item["document_id"],
                }
            }
        )
        operations.append(
            {
                "doc": item["document"],
                "doc_as_upsert": item.get("upsert", True),
            }
        )

    try:
        response = es.bulk(
            operations=operations,
            refresh="wait_for",
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_write_error(
            message="Bulk update request failed",
            status_code=_extract_error_status(exc),
            failures=[
                {
                    "id": None,
                    "status": _extract_error_status(exc),
                    "error": _extract_error_body(exc),
                }
            ],
        )

    raw_items = response.get("items", [])
    results: List[Dict[str, Any]] = []
    failed_items: List[Dict[str, Any]] = []

    for item in raw_items:
        update_result = item.get("update", {})
        result = {
            "id": update_result.get("_id"),
            "result": update_result.get("result", "updated"),
        }

        if "error" in update_result:
            failed_items.append(
                {
                    "id": update_result.get("_id"),
                    "status": update_result.get("status"),
                    "error": update_result.get("error"),
                }
            )

        results.append(result)

    if response.get("errors"):
        _raise_write_error(
            status_code=500,
            message="Bulk update failed for one or more documents",
            failures=failed_items,
        )

    return results
