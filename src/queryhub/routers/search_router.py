from typing import Any, Dict

from fastapi import APIRouter, Body, Depends

from queryhub.constants.actions import Actions
from queryhub.constants.views import Views
from queryhub.database.elasticsearch.getsearchdata import fetch_page
from queryhub.es_query_coverter.model.es_query import QueryParams
from queryhub.es_query_coverter.utils.es_query_builder import ESQueryBuilder
from queryhub.model.base_mapper import map_to_model
from queryhub.model.client_model import Client
from queryhub.service.client_service import update_last_used
from queryhub.utils.auth_dependency import get_current_client
from queryhub.utils.authorization import authorize

router = APIRouter()


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

    return {
        "view": view_name.value,
        "count": len(results),
        "data": [result.model_dump(by_alias=True) for result in results],
        "pagination": {
            "page": params.pagination.page if params.pagination else 0,
            "size": size,
            "offset": offset,
            "returned": len(results),
            "total": total,
        },
        "client": client.client_id,
    }
