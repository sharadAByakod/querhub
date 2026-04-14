from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from constants.actions import Actions
from constants.views import Views
from database.elasticsearch.getsearchdata import fetch_page
from database.elasticsearch.writesearchdata import write_document, write_documents
from es_query_coverter.model.es_query import QueryParams
from es_query_coverter.model.update_request import UpdateRequest
from es_query_coverter.model.write_request import WriteRequest
from es_query_coverter.utils.es_query_builder import ESQueryBuilder
from es_query_coverter.utils.write_helpers import WriteHelpers
from model.base_mapper import map_to_model
from model.client_model import Client, TokenRequest
from service.client_service import authenticate_client, update_last_used
from utils.auth_dependency import get_current_client
from utils.authorization import authorize
from utils.security import create_access_token

router = APIRouter()

PIT_KEEP_ALIVE = "1m"
BATCH_SIZE = 1000


@router.post(
    "/token",
    tags=["Auth"],
    summary="Generate access token",
    description="Exchange Client ID and Secret for a Bearer JWT.",
)
async def generate_token_api(
    params: TokenRequest = Body(...),
) -> Dict[str, Any]:
    """
    Exchanges a client_id/client_secret pair for a valid JWT token.
    """
    client = authenticate_client(params)
    if not client:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials or inactive account",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate token payload
    # The 'sub' claim is mandatory for our auth dependency
    token_payload = {
        "sub": client.client_id,
        "owner": client.owner,
    }

    access_token = create_access_token(token_payload)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 30,  # match default expiration
    }


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

    resolved_document_id = document_id or params.document_id
    result = write_document(
        index=view_name.index_name,
        document=validated_document,
        document_id=resolved_document_id,
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
    "/search/view/{view_name}",
    tags=["Search"],
    summary="Search within a specific view",
    description="Generic search endpoint supporting complex filters, pagination, and sorting.",
)
async def generic_view_api(
    view_name: Views,
    params: QueryParams = Body(default_factory=QueryParams),  # noqa: B008
    client: Client = Depends(get_current_client),  # noqa: B008
) -> Dict[str, Any]:
    """
    Generic API for all views using dynamic ES query builder.
    Returns a single paginated result set.
    """

    authorize(view_name, Actions.READ, client)
    update_last_used(client.client_id)

    builder = ESQueryBuilder(view_name.model)

    size, offset = builder.build_pagination(params.pagination)
    es_sort = builder.build_sort(params.sort)
    es_filters = builder.build_filters(params.filters)
    es_source = builder.build_source(params.source)

    hits, total = fetch_page(
        index=view_name.index_name,
        query=es_filters if es_filters else None,
        sort=es_sort,
        source=es_source,
        size=size,
        offset=offset,
    )

    results = [map_to_model(view_name.model, hit["_source"]) for hit in hits]

    # aggs = None
    # if params.aggs:
    #    aggs = fetch_aggs(
    #        index=view_name.index_name,
    #        query=es_filters["bool"] if es_filters else None,
    #        aggs=params.aggs,
    #    )

    return {
        "view": view_name.value,
        "count": len(results),
        "data": [r.model_dump(by_alias=True) for r in results],
        "pagination": {
            "page": params.pagination.page if params.pagination else 0,
            "size": size,
            "offset": offset,
            "returned": len(results),
            "total": total,
        },
        # "aggregations": aggs,
        "client": client.client_id,
    }


@router.post(
    "/write/view/{view_name}",
    tags=["Write"],
    summary="Create or replace a document",
    description="Generic write API for view-backed documents. Validates fields against model allowlists.",
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
    description="Convenience endpoint for updating a document where the ID is part of the URL path.",
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
