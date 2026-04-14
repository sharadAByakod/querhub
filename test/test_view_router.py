import asyncio
import importlib
import sys
import types

import pytest

from constants.views import Views
from es_query_coverter.model.es_query import QueryParams
from es_query_coverter.model.update_request import UpdateRequest
from es_query_coverter.model.write_request import WriteRequest
from model.client_model import Client

fake_auth_dependency = types.ModuleType("utils.auth_dependency")
fake_auth_dependency.get_current_client = lambda: None
sys.modules.setdefault("utils.auth_dependency", fake_auth_dependency)

fake_client_service = types.ModuleType("service.client_service")
fake_client_service.authenticate_client = lambda *args, **kwargs: None
fake_client_service.update_last_used = lambda *args, **kwargs: None
sys.modules.setdefault("service.client_service", fake_client_service)

fake_security = types.ModuleType("utils.security")
fake_security.create_access_token = lambda *args, **kwargs: "token"
sys.modules.setdefault("utils.security", fake_security)

view_router = importlib.import_module("routers.view_router")


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

    monkeypatch.setattr(view_router, "fetch_page", fake_fetch_page)
    monkeypatch.setattr(view_router, "authorize", lambda *args, **kwargs: None)
    monkeypatch.setattr(view_router, "update_last_used", lambda *args, **kwargs: None)

    payload = asyncio.run(
        view_router.generic_view_api(
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


def test_generic_view_write_api_validates_allowed_fields(monkeypatch):
    captured: dict = {}

    def fake_write_document(**kwargs):
        captured.update(kwargs)
        return {
            "id": "doc-1",
            "result": "updated",
        }

    monkeypatch.setattr(view_router, "write_document", fake_write_document)
    monkeypatch.setattr(view_router, "authorize", lambda *args, **kwargs: None)
    monkeypatch.setattr(view_router, "update_last_used", lambda *args, **kwargs: None)

    payload = asyncio.run(
        view_router.generic_view_write_api(
            view_name=Views.VULNIQ_ITSM,
            params=WriteRequest.model_validate(
                {
                    "document_id": "doc-1",
                    "upsert": True,
                    "document": {
                        "host.count": "5",
                        "vulnerability.summary": "Kernel issue",
                        "organization.id": "ORG-1",
                    },
                }
            ),
            client=Client(
                client_id="client-1",
                client_secret="secret",
                permissions={"vulnitsm": ["write"]},
            ),
        )
    )

    assert captured == {
        "index": Views.VULNIQ_ITSM.index_name,
        "document": {
            "host.count": 5,
            "vulnerability.summary": "Kernel issue",
            "organization.id": "ORG-1",
        },
        "document_id": "doc-1",
        "upsert": True,
    }
    assert payload["view"] == "vulnitsm"
    assert payload["action"] == "write"
    assert payload["document_id"] == "doc-1"
    assert payload["result"] == "updated"
    assert payload["written_fields"] == [
        "host.count",
        "organization.id",
        "vulnerability.summary",
    ]
    assert "organization.id" in payload["allowed_fields"]
    assert "host.count" in payload["allowed_fields"]


def test_generic_view_update_api_accepts_document_id_in_body(monkeypatch):
    captured: dict = {}

    def fake_write_document(**kwargs):
        captured.update(kwargs)
        return {
            "id": "doc-2",
            "result": "updated",
        }

    monkeypatch.setattr(view_router, "write_document", fake_write_document)
    monkeypatch.setattr(view_router, "authorize", lambda *args, **kwargs: None)
    monkeypatch.setattr(view_router, "update_last_used", lambda *args, **kwargs: None)

    payload = asyncio.run(
        view_router.generic_view_update_api(
            view_name=Views.VULNIQ_ITSM,
            params=UpdateRequest.model_validate(
                {
                    "document_id": "doc-2",
                    "upsert": True,
                    "document": {
                        "host.ip": "10.10.1.14",
                        "vulnerability.summary": "Updated summary",
                    },
                }
            ),
            client=Client(
                client_id="client-1",
                client_secret="secret",
                permissions={"vulnitsm": ["write"]},
            ),
        )
    )

    assert captured["document_id"] == "doc-2"
    assert payload["action"] == "update"
    assert payload["document_id"] == "doc-2"


def test_generic_view_update_api_accepts_multiple_ids_with_own_docs(monkeypatch):
    captured: dict = {}

    def fake_write_documents(**kwargs):
        captured.update(kwargs)
        return [
            {
                "id": "doc-2",
                "result": "updated",
            },
            {
                "id": "doc-3",
                "result": "updated",
            },
        ]

    monkeypatch.setattr(view_router, "write_documents", fake_write_documents)
    monkeypatch.setattr(view_router, "authorize", lambda *args, **kwargs: None)
    monkeypatch.setattr(view_router, "update_last_used", lambda *args, **kwargs: None)

    payload = asyncio.run(
        view_router.generic_view_update_api(
            view_name=Views.VULNIQ_ITSM,
            params=UpdateRequest.model_validate(
                {
                    "updates": [
                        {
                            "document_id": "doc-2",
                            "upsert": True,
                            "document": {
                                "host.count": "5",
                                "vulnerability.summary": "Updated summary",
                            },
                        },
                        {
                            "document_id": "doc-3",
                            "upsert": False,
                            "document": {
                                "organization.id": "ORG-2",
                                "host.ip": "10.10.1.15",
                            },
                        },
                    ]
                }
            ),
            client=Client(
                client_id="client-1",
                client_secret="secret",
                permissions={"vulnitsm": ["write"]},
            ),
        )
    )

    assert captured == {
        "index": Views.VULNIQ_ITSM.index_name,
        "updates": [
            {
                "document_id": "doc-2",
                "document": {
                    "host.count": 5,
                    "vulnerability.summary": "Updated summary",
                },
                "upsert": True,
            },
            {
                "document_id": "doc-3",
                "document": {
                    "organization.id": "ORG-2",
                    "host.ip": "10.10.1.15",
                },
                "upsert": False,
            },
        ],
    }
    assert payload["action"] == "update"
    assert payload["count"] == 2
    assert payload["results"] == [
        {
            "document_id": "doc-2",
            "result": "updated",
            "written_fields": [
                "host.count",
                "vulnerability.summary",
            ],
        },
        {
            "document_id": "doc-3",
            "result": "updated",
            "written_fields": [
                "host.ip",
                "organization.id",
            ],
        },
    ]


def test_generic_view_update_by_id_api_uses_path_document_id(monkeypatch):
    captured: dict = {}

    def fake_write_document(**kwargs):
        captured.update(kwargs)
        return {
            "id": "doc-3",
            "result": "updated",
        }

    monkeypatch.setattr(view_router, "write_document", fake_write_document)
    monkeypatch.setattr(view_router, "authorize", lambda *args, **kwargs: None)
    monkeypatch.setattr(view_router, "update_last_used", lambda *args, **kwargs: None)

    payload = asyncio.run(
        view_router.generic_view_update_by_id_api(
            view_name=Views.VULNIQ_ITSM,
            document_id="doc-3",
            params=WriteRequest.model_validate(
                {
                    "upsert": True,
                    "document": {
                        "host.count": 8,
                        "organization.id": "ORG-1",
                    },
                }
            ),
            client=Client(
                client_id="client-1",
                client_secret="secret",
                permissions={"vulnitsm": ["write"]},
            ),
        )
    )

    assert captured["document_id"] == "doc-3"
    assert payload["action"] == "update"
    assert payload["document_id"] == "doc-3"


def test_generic_view_update_by_id_api_rejects_mismatched_body_id(monkeypatch):
    monkeypatch.setattr(view_router, "authorize", lambda *args, **kwargs: None)
    monkeypatch.setattr(view_router, "update_last_used", lambda *args, **kwargs: None)

    with pytest.raises(view_router.HTTPException) as exc_info:
        asyncio.run(
            view_router.generic_view_update_by_id_api(
                view_name=Views.VULNIQ_ITSM,
                document_id="doc-3",
                params=WriteRequest.model_validate(
                    {
                        "document_id": "doc-9",
                        "upsert": True,
                        "document": {
                            "host.count": 8,
                        },
                    }
                ),
                client=Client(
                    client_id="client-1",
                    client_secret="secret",
                    permissions={"vulnitsm": ["write"]},
                ),
            )
        )

    assert exc_info.value.status_code == 400
    assert "document_id mismatch" in str(exc_info.value.detail)
