import pytest
from fastapi import HTTPException

from database.elasticsearch import writesearchdata


def test_write_document_normalizes_single_update_failure(monkeypatch):
    class FakeError(Exception):
        def __init__(self):
            self.meta = type("Meta", (), {"status": 409})()
            self.body = {
                "error": {
                    "type": "version_conflict_engine_exception",
                    "reason": "[doc-1]: version conflict",
                }
            }
            super().__init__("version conflict")

    class FakeES:
        def update(self, **kwargs):
            raise FakeError()

    monkeypatch.setattr(writesearchdata, "get_es", lambda: FakeES())

    with pytest.raises(HTTPException) as exc_info:
        writesearchdata.write_document(
            index="test-index",
            document={"host.count": 4},
            document_id="doc-1",
            upsert=False,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == {
        "message": "Write request failed",
        "failures": [
            {
                "id": "doc-1",
                "status": 409,
                "error": {
                    "error": {
                        "type": "version_conflict_engine_exception",
                        "reason": "[doc-1]: version conflict",
                    }
                },
            }
        ],
    }


def test_write_documents_uses_bulk_operations(monkeypatch):
    captured: dict = {}

    class FakeES:
        def bulk(self, **kwargs):
            captured.update(kwargs)
            return {
                "errors": False,
                "items": [
                    {
                        "update": {
                            "_id": "doc-1",
                            "result": "updated",
                            "status": 200,
                        }
                    },
                    {
                        "update": {
                            "_id": "doc-2",
                            "result": "created",
                            "status": 201,
                        }
                    },
                ],
            }

    monkeypatch.setattr(writesearchdata, "get_es", lambda: FakeES())

    result = writesearchdata.write_documents(
        index="test-index",
        updates=[
            {
                "document_id": "doc-1",
                "document": {"host.count": 4},
                "upsert": True,
            },
            {
                "document_id": "doc-2",
                "document": {"organization.id": "ORG-2"},
                "upsert": False,
            },
        ],
    )

    assert captured == {
        "operations": [
            {"update": {"_index": "test-index", "_id": "doc-1"}},
            {"doc": {"host.count": 4}, "doc_as_upsert": True},
            {"update": {"_index": "test-index", "_id": "doc-2"}},
            {"doc": {"organization.id": "ORG-2"}, "doc_as_upsert": False},
        ],
        "refresh": "wait_for",
    }
    assert result == [
        {"id": "doc-1", "result": "updated"},
        {"id": "doc-2", "result": "created"},
    ]


def test_write_documents_raises_on_bulk_item_failure(monkeypatch):
    class FakeES:
        def bulk(self, **kwargs):
            return {
                "errors": True,
                "items": [
                    {
                        "update": {
                            "_id": "doc-1",
                            "result": "updated",
                            "status": 200,
                        }
                    },
                    {
                        "update": {
                            "_id": "doc-2",
                            "status": 404,
                            "error": {
                                "type": "document_missing_exception",
                                "reason": "[doc-2]: document missing",
                            },
                        }
                    },
                ],
            }

    monkeypatch.setattr(writesearchdata, "get_es", lambda: FakeES())

    with pytest.raises(HTTPException) as exc_info:
        writesearchdata.write_documents(
            index="test-index",
            updates=[
                {
                    "document_id": "doc-1",
                    "document": {"host.count": 4},
                    "upsert": True,
                },
                {
                    "document_id": "doc-2",
                    "document": {"host.count": 7},
                    "upsert": False,
                },
            ],
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == {
        "message": "Bulk update failed for one or more documents",
        "failures": [
            {
                "id": "doc-2",
                "status": 404,
                "error": {
                    "type": "document_missing_exception",
                    "reason": "[doc-2]: document missing",
                },
            }
        ],
    }


def test_write_documents_normalizes_top_level_bulk_failure(monkeypatch):
    class FakeError(Exception):
        def __init__(self):
            self.meta = type("Meta", (), {"status": 503})()
            self.body = {
                "error": {
                    "type": "unavailable_shards_exception",
                    "reason": "primary shard is not active",
                }
            }
            super().__init__("bulk unavailable")

    class FakeES:
        def bulk(self, **kwargs):
            raise FakeError()

    monkeypatch.setattr(writesearchdata, "get_es", lambda: FakeES())

    with pytest.raises(HTTPException) as exc_info:
        writesearchdata.write_documents(
            index="test-index",
            updates=[
                {
                    "document_id": "doc-1",
                    "document": {"host.count": 4},
                    "upsert": True,
                }
            ],
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == {
        "message": "Bulk update request failed",
        "failures": [
            {
                "id": None,
                "status": 503,
                "error": {
                    "error": {
                        "type": "unavailable_shards_exception",
                        "reason": "primary shard is not active",
                    }
                },
            }
        ],
    }
