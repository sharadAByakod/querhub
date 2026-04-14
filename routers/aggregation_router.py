from typing import Any, Dict

from fastapi import APIRouter, Body, Depends

from constants.actions import Actions
from constants.views import Views
from database.elasticsearch.getaggsdata import fetch_aggs
from es_query_coverter.aggregations.models import AggregationQueryParams
from es_query_coverter.aggregations.agg_builder import ESAggregationBuilder
from es_query_coverter.utils.es_query_builder import ESQueryBuilder
from es_query_coverter.utils.simple_query_parser import parse_simple_where
from model.client_model import Client
from service.client_service import update_last_used
from utils.auth_dependency import get_current_client
from utils.authorization import authorize

router = APIRouter()


@router.post(
    "/aggs/view/{view_name}",
    tags=["Aggregations"],
    summary="Get aggregations for a view",
    description="Calculate metrics and buckets based on a view model and optional filters.",
)
async def generic_aggregation_api(
    view_name: Views,
    params: AggregationQueryParams = Body(...),
    client: Client = Depends(get_current_client),
) -> Dict[str, Any]:
    """
    Generic Aggregation API for all views.
    """

    authorize(view_name, Actions.READ, client)
    update_last_used(client.client_id)

    # 1. Build Query (Filters)
    query_builder = ESQueryBuilder(view_name.model)

    # Support simple 'where' if filters not provided
    if not params.filters and params.where:
        params.filters = parse_simple_where(params.where)

    es_filters = query_builder.build_filters(params.filters)

    # 2. Build Aggregations
    agg_builder = ESAggregationBuilder(view_name.model)
    es_aggs = agg_builder.build(params.aggs)

    # 3. Fetch from ES
    result = fetch_aggs(
        index=view_name.index_name,
        aggs=es_aggs,
        query=es_filters if es_filters else None,
    )

    return {
        "view": view_name.value,
        "aggregations": result,
        "client": client.client_id,
    }
