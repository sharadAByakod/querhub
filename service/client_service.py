from datetime import datetime

from elasticsearch import NotFoundError

from constants.es_indices import EsIndices
from database.elasticsearch.elastic import get_es
from model.client_model import Client, TokenRequest
from utils.security import verify_secret


def get_client(client_id: str) -> Client | None:
    es = get_es()
    try:
        response = es.get(index=EsIndices.API_CLIENT.value, id=client_id)
    except NotFoundError:
        return None

    source = response.get("_source")
    if source:
        return Client.model_validate({"client_id": client_id, **source})
    return None


def authenticate_client(request: TokenRequest) -> Client | None:
    """
    Verify client_id and client_secret.
    """
    client = get_client(request.client_id)
    if not client:
        return None

    # Verify hashed secret
    if not verify_secret(request.client_secret, client.client_secret):
        return None

    if client.status != "active":
        return None

    return client


def create_client(client: Client) -> None:
    es = get_es()
    es.index(
        index=EsIndices.API_CLIENT.value,
        id=client.client_id,
        document=client.model_dump(),
    )
    return None


def approve_client(client_id: str) -> None:
    es = get_es()
    es.update(
        index=EsIndices.API_CLIENT.value,
        id=client_id,
        doc={"last_used": datetime.utcnow()},
    )
    return None


def update_last_used(client_id: str) -> None:
    es = get_es()
    es.update(
        index=EsIndices.API_CLIENT.value,
        id=client_id,
        doc={"last_used": datetime.utcnow()},
    )
    return None
