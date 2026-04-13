from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from model.client_model import Client
from service.client_service import get_client
from utils.security import decode_token

security = HTTPBearer()


def get_current_client(
    credentials: HTTPAuthorizationCredentials = Depends(security),  # noqa
) -> Client:  #
    try:
        token = credentials.credentials
        payload = decode_token(token)
        client_id = payload.get("sub")
        if not client_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        client = get_client(client_id)
        if not client:
            raise HTTPException(status_code=401, detail="Client not found")
        if client.status != "active":
            raise HTTPException(status_code=403, detail="Client not active")
        return client
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
