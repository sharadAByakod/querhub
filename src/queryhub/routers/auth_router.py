from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException

from queryhub.model.client_model import TokenRequest
from queryhub.service.client_service import authenticate_client
from queryhub.utils.security import ACCESS_TOKEN_EXPIRE, create_access_token

router = APIRouter()


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

    token_payload = {
        "sub": client.client_id,
        "owner": client.owner,
    }
    access_token = create_access_token(token_payload)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE,
    }
