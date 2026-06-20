from typing import Optional

from elasticsearch import Elasticsearch

from config.settings import settings

_es_client: Optional[Elasticsearch] = None


def connect_elasticsearch() -> Elasticsearch:
    """
    Initialize the Elasticsearch client if not already created.
    Safe for repeated calls.
    """
    global _es_client

    _es_client = Elasticsearch(
        hosts=[settings.es_host],
        basic_auth=(settings.es_user, settings.es_pass),
        ca_certs=settings.es_ca_path,
        verify_certs=True,
        client_cert=settings.es_client_cert,
        client_key=settings.es_client_key,
        request_timeout=10,
    )

    return _es_client


def get_es() -> Elasticsearch:
    """
    Always return an initialized Elasticsearch client.
    Raises if connect_elasticsearch() was never called.
    """
    if _es_client is None:
        # auto initialize instead of throwing error
        return connect_elasticsearch()

    return _es_client
