import pytest
from fastapi import HTTPException

from es_query_coverter.utils.write_helpers import WriteHelpers
from model.vulniqitsm_model import VulniqItsm


def test_validate_write_document_accepts_writable_alias_fields():
    result = WriteHelpers.validate_write_document(
        VulniqItsm,
        {
            "host.count": "7",
            "vulnerability.summary": "Kernel issue",
            "organization.id": "ORG-1",
            "host.ip": "10.10.1.14",
        },
    )

    assert result == {
        "host.count": 7,
        "vulnerability.summary": "Kernel issue",
        "organization.id": "ORG-1",
        "host.ip": "10.10.1.14",
    }


def test_validate_write_document_rejects_non_writable_field():
    with pytest.raises(HTTPException) as exc_info:
        WriteHelpers.validate_write_document(
            VulniqItsm,
            {
                "monitoring.cluster.name": "cluster-a",
            },
        )

    assert exc_info.value.status_code == 400
    assert "not writable" in str(exc_info.value.detail)


def test_validate_write_document_rejects_unknown_field():
    with pytest.raises(HTTPException) as exc_info:
        WriteHelpers.validate_write_document(
            VulniqItsm,
            {
                "bad.field": "value",
            },
        )

    assert exc_info.value.status_code == 400
    assert "Invalid write field" in str(exc_info.value.detail)


def test_writable_fields_for_includes_inherited_model_fields():
    writable_fields = WriteHelpers.writable_fields_for(VulniqItsm)

    assert "organization.id" in writable_fields
    assert "host.ip" in writable_fields
    assert "vulnerability.summary" in writable_fields
    assert "host.count" in writable_fields
