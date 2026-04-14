from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from model.client_model import Client
from service.client_service import get_client
from utils.security import decode_token

security = HTTPBearer()


from jose import JWTError, ExpiredSignatureError


def get_current_client(
    credentials: HTTPAuthorizationCredentials = Depends(security),  # noqa
) -> Client:  #
    try:
        token = credentials.credentials
        payload = decode_token(token)
        client_id = payload.get("sub")

        if not client_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing sub claim")

        client = get_client(client_id)

        if not client:
            raise HTTPException(status_code=401, detail="Client not found in system")

        if client.status != "active":
            raise HTTPException(status_code=403, detail="Client account is inactive")

        return client

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token signature or format")
    except HTTPException:
        raise  # re-raise our own errors
    except Exception as e:
        # log but don't leak internals
        print(f"Auth system error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal authentication failure")
