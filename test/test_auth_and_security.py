import importlib.util
import sys
from pathlib import Path

import pytest
from elasticsearch import NotFoundError
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from constants.actions import Actions
from constants.views import Views
from model.client_model import Client

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module(module_name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(
        module_name,
        REPO_ROOT / relative_path,
    )
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_actual_security_module():
    return _load_module("security_actual", "utils/security.py")


def _load_actual_client_service_module(monkeypatch):
    security_module = _load_actual_security_module()
    monkeypatch.setitem(sys.modules, "utils.security", security_module)
    return _load_module("client_service_actual", "service/client_service.py")


def _load_actual_authorization_module():
    return _load_module("authorization_actual", "utils/authorization.py")


def _load_actual_auth_dependency_module(monkeypatch):
    security_module = _load_actual_security_module()
    client_service_module = _load_actual_client_service_module(monkeypatch)
    monkeypatch.setitem(sys.modules, "utils.security", security_module)
    monkeypatch.setitem(sys.modules, "service.client_service", client_service_module)
    return _load_module("auth_dependency_actual", "utils/auth_dependency.py")


@pytest.mark.parametrize("permission_key", ["vulnitsm", "VULNIQ_ITSM"])
def test_authorize_normalizes_view_keys_and_action_values(permission_key):
    authorization = _load_actual_authorization_module()
    client = Client(
        client_id="client-1",
        client_secret="secret",
        permissions={permission_key: ["READ", "write"]},
    )

    authorization.authorize(Views.VULNIQ_ITSM, Actions.READ, client)
    authorization.authorize(Views.VULNIQ_ITSM, Actions.WRITE, client)


def test_get_client_returns_none_when_document_missing(monkeypatch):
    client_service = _load_actual_client_service_module(monkeypatch)

    class FakeES:
        def get(self, **kwargs):
            raise NotFoundError(
                message="missing",
                meta=type("Meta", (), {"status": 404})(),
                body={"found": False},
            )

    monkeypatch.setattr(client_service, "get_es", lambda: FakeES())

    assert client_service.get_client("missing-client") is None


def test_get_current_client_returns_401_when_client_is_missing(monkeypatch):
    auth_dependency = _load_actual_auth_dependency_module(monkeypatch)
    monkeypatch.setattr(auth_dependency, "decode_token", lambda _: {"sub": "missing-client"})
    monkeypatch.setattr(auth_dependency, "get_client", lambda _: None)

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="test-token",
    )

    with pytest.raises(HTTPException) as exc_info:
        auth_dependency.get_current_client(credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Client not found in system"


def test_load_access_token_expire_casts_env_value_to_int(monkeypatch):
    security = _load_actual_security_module()
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE", "45")

    assert security._load_access_token_expire() == 45


def test_load_access_token_expire_rejects_invalid_env_value(monkeypatch):
    security = _load_actual_security_module()
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE", "abc")

    with pytest.raises(RuntimeError) as exc_info:
        security._load_access_token_expire()

    assert "ACCESS_TOKEN_EXPIRE" in str(exc_info.value)
