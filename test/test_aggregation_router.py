import asyncio
import importlib
import sys
import types

from constants.views import Views
from es_query_coverter.aggregations.models import (
    AggregationQueryParams,
    AggregationRequest,
    TermsAggregation,
)
from model.client_model import Client

# Mock dependencies
fake_auth_dependency = types.ModuleType("utils.auth_dependency")
fake_auth_dependency.get_current_client = lambda: None
sys.modules["utils.auth_dependency"] = fake_auth_dependency

fake_client_service = types.ModuleType("service.client_service")
fake_client_service.update_last_used = lambda *args, **kwargs: None
fake_client_service.authenticate_client = lambda *args, **kwargs: None
sys.modules["service.client_service"] = fake_client_service

fake_authorization = types.ModuleType("utils.authorization")
fake_authorization.authorize = lambda *args, **kwargs: None
sys.modules["utils.authorization"] = fake_authorization

# Import the router
aggregation_router = importlib.import_module("routers.aggregation_router")


def test_generic_aggregation_api_builds_query_and_aggs(monkeypatch):
    captured: dict = {}

    def fake_fetch_aggs(**kwargs):
        captured.update(kwargs)
        return {
            "severity_counts": {
                "buckets": [
                    {"key": "HIGH", "doc_count": 10},
                    {"key": "CRITICAL", "doc_count": 5},
                ]
            }
        }

    monkeypatch.setattr(aggregation_router, "fetch_aggs", fake_fetch_aggs)
    monkeypatch.setattr(aggregation_router, "authorize", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        aggregation_router,
        "update_last_used",
        lambda *args, **kwargs: None,
    )

    params = AggregationQueryParams(
        where={"all": [{"organization.id": "ORG-1"}]},
        aggs=AggregationRequest(
            terms=[
                TermsAggregation(
                    field="vulnerability.asi_severity",
                    name="severity_counts",
                )
            ]
        )
    )

    client = Client(
        client_id="client-1",
        client_secret="secret",
        permissions={"vulnitsm": ["read"]},
    )

    response = asyncio.run(
        aggregation_router.generic_aggregation_api(
            view_name=Views.VULNIQ_ITSM,
            params=params,
            client=client,
        )
    )

    assert captured["index"] == Views.VULNIQ_ITSM.index_name
    assert captured["query"] == {
        "bool": {
            "must": [{"term": {"organization.id": "ORG-1"}}]
        }
    }
    assert "severity_counts" in captured["aggs"]
    assert (
        captured["aggs"]["severity_counts"]["terms"]["field"]
        == "vulnerability.asi_severity"
    )

    assert response["view"] == Views.VULNIQ_ITSM.value
    assert "severity_counts" in response["aggregations"]
    assert response["client"] == "client-1"
