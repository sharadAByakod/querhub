from typing import Any, Dict, List, Optional

from database.elasticsearch.elastic import get_es


def write_document(
    *,
    index: str,
    document: Dict[str, Any],
    document_id: Optional[str] = None,
    upsert: bool = True,
) -> Dict[str, Any]:
    es = get_es()

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


def write_documents(
    *,
    index: str,
    updates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    for item in updates:
        results.append(
            write_document(
                index=index,
                document=item["document"],
                document_id=item["document_id"],
                upsert=item.get("upsert", True),
            )
        )

    return results
