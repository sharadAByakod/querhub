from typing import Optional

from elasticsearch import Elasticsearch

from config.settings import (  # noqa
    ES_CA_PATH,
    ES_CLIENT_CERT,
    ES_CLIENT_KEY,
    ES_HOST,
    ES_PASS,
    ES_USER,
)

_es_client: Optional[Elasticsearch] = None


def connect_elasticsearch() -> Elasticsearch:
    """
    Initialize the Elasticsearch client if not already created.
    Safe for repeated calls.
    """
    global _es_client

    _es_client = Elasticsearch(
        hosts=[ES_HOST],
        basic_auth=(ES_USER, ES_PASS),
        ca_certs=ES_CA_PATH,
        verify_certs=True,
        client_cert=ES_CLIENT_CERT,
        client_key=ES_CLIENT_KEY,
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
