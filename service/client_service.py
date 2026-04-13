from datetime import datetime

from constants.es_indices import EsIndices
from database.elasticsearch.elastic import get_es
from model.client_model import Client


def get_client(client_id: str) -> Client | None:
    es = get_es()
    response = es.get(index=EsIndices.API_CLIENT.value, id=client_id)

    source = response.get("_source")
    if source:
        return Client(**source)
    return None


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
