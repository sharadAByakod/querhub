from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from queryhub.constants.actions import Actions
from queryhub.constants.views import Views
from queryhub.database.elasticsearch.writesearchdata import write_document, write_documents
from queryhub.es_query_coverter.model.update_request import UpdateRequest
from queryhub.es_query_coverter.model.write_request import WriteRequest
from queryhub.es_query_coverter.utils.write_helpers import WriteHelpers
from queryhub.model.client_model import Client
from queryhub.service.client_service import update_last_used
from queryhub.utils.auth_dependency import get_current_client
from queryhub.utils.authorization import authorize

router = APIRouter()


def _write_view_document(
    *,
    view_name: Views,
    params: WriteRequest,
    client: Client,
    document_id: Optional[str] = None,
    action: str = "write",
) -> Dict[str, Any]:
    authorize(view_name, Actions.WRITE, client)
    update_last_used(client.client_id)

    if document_id and params.document_id and params.document_id != document_id:
        raise HTTPException(
            status_code=400,
            detail=(
                f"document_id mismatch: path id '{document_id}' "
                f"does not match body id '{params.document_id}'"
            ),
        )

    validated_document = WriteHelpers.validate_write_document(
        view_name.model,
        params.document,
    )

    result = write_document(
        index=view_name.index_name,
        document=validated_document,
        document_id=document_id or params.document_id,
        upsert=params.upsert,
    )

    return {
        "view": view_name.value,
        "action": action,
        "document_id": result["id"],
        "result": result["result"],
        "written_fields": sorted(validated_document),
        "allowed_fields": WriteHelpers.writable_fields_for(view_name.model),
        "client": client.client_id,
    }


def _validate_write_payload(
    *,
    view_name: Views,
    document: Dict[str, Any],
    document_id: Optional[str],
    upsert: bool,
) -> Dict[str, Any]:
    validated_document = WriteHelpers.validate_write_document(
        view_name.model,
        document,
    )

    return {
        "document_id": document_id,
        "document": validated_document,
        "upsert": upsert,
        "written_fields": sorted(validated_document),
    }


@router.post(
    "/write/view/{view_name}",
    tags=["Write"],
    summary="Create or replace a document",
    description=(
        "Generic write API for view-backed documents. "
        "Validates fields against model allowlists."
    ),
)
async def generic_view_write_api(
    view_name: Views,
    params: WriteRequest = Body(...),  # noqa: B008
    client: Client = Depends(get_current_client),  # noqa: B008
) -> Dict[str, Any]:
    """
    Generic write API for view-backed documents.
    Accepts flat Elasticsearch field aliases and validates them against the model allowlist.
    """

    return _write_view_document(
        view_name=view_name,
        params=params,
        client=client,
        action="write",
    )


@router.post(
    "/update/view/{view_name}",
    tags=["Write"],
    summary="Update one or more documents",
    description="Bulk or single update API. Accepts multiple document_id/document pairs.",
)
async def generic_view_update_api(
    view_name: Views,
    params: UpdateRequest = Body(...),  # noqa: B008
    client: Client = Depends(get_current_client),  # noqa: B008
) -> Dict[str, Any]:
    """
    Generic update API for view-backed documents.
    Accepts either one id/document pair or multiple id/document pairs.
    """
    authorize(view_name, Actions.WRITE, client)
    update_last_used(client.client_id)

    allowed_fields = WriteHelpers.writable_fields_for(view_name.model)

    if params.updates:
        validated_updates = [
            _validate_write_payload(
                view_name=view_name,
                document=item.document,
                document_id=item.document_id,
                upsert=item.upsert,
            )
            for item in params.updates
        ]

        results = write_documents(
            index=view_name.index_name,
            updates=[
                {
                    "document_id": item["document_id"],
                    "document": item["document"],
                    "upsert": item["upsert"],
                }
                for item in validated_updates
            ],
        )

        return {
            "view": view_name.value,
            "action": "update",
            "count": len(results),
            "results": [
                {
                    "document_id": result["id"],
                    "result": result["result"],
                    "written_fields": validated_item["written_fields"],
                }
                for validated_item, result in zip(validated_updates, results)
            ],
            "allowed_fields": allowed_fields,
            "client": client.client_id,
        }

    validated_payload = _validate_write_payload(
        view_name=view_name,
        document=params.document or {},
        document_id=params.document_id,
        upsert=params.upsert,
    )

    result = write_document(
        index=view_name.index_name,
        document=validated_payload["document"],
        document_id=validated_payload["document_id"],
        upsert=validated_payload["upsert"],
    )

    return {
        "view": view_name.value,
        "action": "update",
        "document_id": result["id"],
        "result": result["result"],
        "written_fields": validated_payload["written_fields"],
        "allowed_fields": allowed_fields,
        "client": client.client_id,
    }


@router.post(
    "/update/view/{view_name}/{document_id}",
    tags=["Write"],
    summary="Update a document by path ID",
    description=(
        "Convenience endpoint for updating a document "
        "where the ID is part of the URL path."
    ),
)
async def generic_view_update_by_id_api(
    view_name: Views,
    document_id: str,
    params: WriteRequest = Body(...),  # noqa: B008
    client: Client = Depends(get_current_client),  # noqa: B008
) -> Dict[str, Any]:
    """
    Generic update API for view-backed documents using the document id from the path.
    """

    return _write_view_document(
        view_name=view_name,
        params=params,
        client=client,
        document_id=document_id,
        action="update",
    )
