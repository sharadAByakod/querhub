from typing import Optional
from urllib.parse import urlparse

from elasticsearch import Elasticsearch

from queryhub.config.settings import settings

_es_client: Optional[Elasticsearch] = None


def connect_elasticsearch() -> Elasticsearch:
    """
    Initialize the Elasticsearch client if not already created.
    Safe for repeated calls.
    """
    global _es_client

    client_options = {
        "hosts": [settings.es_host],
        "basic_auth": (settings.es_user, settings.es_pass),
        "request_timeout": 10,
    }

    if urlparse(settings.es_host).scheme == "https":
        client_options.update(
            {
                "ca_certs": settings.es_ca_path,
                "verify_certs": True,
                "client_cert": settings.es_client_cert,
                "client_key": settings.es_client_key,
            }
        )

    _es_client = Elasticsearch(**client_options)

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
