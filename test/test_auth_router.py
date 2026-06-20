import asyncio
import importlib
import sys
import types

import pytest

from model.client_model import Client, TokenRequest

fake_client_service = types.ModuleType("service.client_service")
fake_client_service.authenticate_client = lambda *args, **kwargs: None
fake_client_service.update_last_used = lambda *args, **kwargs: None
sys.modules["service.client_service"] = fake_client_service

fake_security = types.ModuleType("utils.security")
fake_security.ACCESS_TOKEN_EXPIRE = 30
fake_security.create_access_token = lambda *args, **kwargs: "token"
sys.modules["utils.security"] = fake_security

auth_router = importlib.import_module("routers.auth_router")


def test_generate_token_api_returns_token_payload(monkeypatch):
    monkeypatch.setattr(
        auth_router,
        "authenticate_client",
        lambda params: Client(
            client_id=params.client_id,
            client_secret="hashed-secret",
            owner="security-team",
            status="active",
        ),
    )

    captured: dict = {}

    def fake_create_access_token(payload):
        captured.update(payload)
        return "signed-token"

    monkeypatch.setattr(auth_router, "create_access_token", fake_create_access_token)

    response = asyncio.run(
        auth_router.generate_token_api(
            TokenRequest(client_id="client-1", client_secret="plain-secret")
        )
    )

    assert captured == {
        "sub": "client-1",
        "owner": "security-team",
    }
    assert response == {
        "access_token": "signed-token",
        "token_type": "bearer",
        "expires_in": 30,
    }


def test_generate_token_api_rejects_invalid_credentials(monkeypatch):
    monkeypatch.setattr(auth_router, "authenticate_client", lambda params: None)

    with pytest.raises(auth_router.HTTPException) as exc_info:
        asyncio.run(
            auth_router.generate_token_api(
                TokenRequest(client_id="client-1", client_secret="bad-secret")
            )
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid credentials or inactive account"
