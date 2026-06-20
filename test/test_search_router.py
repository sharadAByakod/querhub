import asyncio
import importlib
import sys
import types

from constants.views import Views
from es_query_coverter.model.es_query import QueryParams
from model.client_model import Client

fake_auth_dependency = types.ModuleType("utils.auth_dependency")
fake_auth_dependency.get_current_client = lambda: None
sys.modules["utils.auth_dependency"] = fake_auth_dependency

fake_client_service = types.ModuleType("service.client_service")
fake_client_service.authenticate_client = lambda *args, **kwargs: None
fake_client_service.update_last_used = lambda *args, **kwargs: None
sys.modules["service.client_service"] = fake_client_service

search_router = importlib.import_module("routers.search_router")


def test_generic_view_api_applies_pagination_and_bool_query(monkeypatch):
    captured: dict = {}

    def fake_fetch_page(**kwargs):
        captured.update(kwargs)
        return (
            [
                {
                    "_source": {
                        "host.ip": "1.2.3.4",
                        "vulnerability.summary": "Kernel issue",
                    }
                }
            ],
            11,
        )

    monkeypatch.setattr(search_router, "fetch_page", fake_fetch_page)
    monkeypatch.setattr(search_router, "authorize", lambda *args, **kwargs: None)
    monkeypatch.setattr(search_router, "update_last_used", lambda *args, **kwargs: None)

    payload = asyncio.run(
        search_router.generic_view_api(
            view_name=Views.VULNIQ_ITSM,
            params=QueryParams.model_validate(
                {
                    "page": 1,
                    "size": 2,
                    "select": ["host.ip", "vulnerability.summary"],
                    "where": {
                        "all": [
                            {
                                "vulnerability.summary": {
                                    "match": "Kernel issue",
                                }
                            }
                        ]
                    },
                    "sort": ["host.ip"],
                }
            ),
            client=Client(
                client_id="client-1",
                client_secret="secret",
                permissions={"vulnitsm": ["read"]},
            ),
        )
    )

    assert captured["query"] == {
        "bool": {
            "must": [{"match": {"vulnerability.summary": "Kernel issue"}}],
        }
    }
    assert captured["size"] == 2
    assert captured["offset"] == 2

    assert payload["pagination"] == {
        "page": 1,
        "size": 2,
        "offset": 2,
        "returned": 1,
        "total": 11,
    }
    assert len(payload["data"]) == 1
    assert payload["data"][0]["host.ip"] == "1.2.3.4"
    assert payload["data"][0]["vulnerability.summary"] == "Kernel issue"
