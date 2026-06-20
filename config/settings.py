import os
from dataclasses import dataclass


def _get_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _get_csv(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    log_level: str
    es_host: str
    es_user: str
    es_pass: str
    es_ca_path: str
    es_client_cert: str
    es_client_key: str
    query_hub_username: str
    query_hub_password: str | None
    scroll_timeout: str
    chunk_size: int
    num_slices: int
    org_name_filter: tuple[str, ...]
    severity_filter: list[str]


settings = Settings(
    log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    es_host=os.getenv("ES_HOST", "http://localhost:9200"),
    es_user=os.getenv("ES_USER", "elastic"),
    es_pass=os.getenv("ES_PASS", "abc"),
    es_ca_path=os.getenv("ES_CA_PATH", "ca.crt"),
    es_client_cert=os.getenv("ES_CLIENT_CERT", "client.crt"),
    es_client_key=os.getenv("ES_CLIENT_KEY", "client.key"),
    query_hub_username=os.getenv("QUERY_HUB_USERNAME", "asi_query_hub"),
    query_hub_password=os.getenv("QUERY_HUB_PASSWORD"),
    scroll_timeout=os.getenv("SCROLL_TIMEOUT", "2m"),
    chunk_size=_get_int("CHUNK_SIZE", 1000),
    num_slices=_get_int("NUM_SLICES", 2),
    org_name_filter=(
        "BT Security - IMPSS Management Systems - Reigate",
        "BT Security - IMPSS Management Systems - Derby",
    ),
    severity_filter=_get_csv("SEVERITY_FILTER", "HIGH,CRITICAL"),
)

# Backwards-compatible module constants.
LOG_LEVEL = settings.log_level
ES_HOST = settings.es_host
ES_USER = settings.es_user
ES_PASS = settings.es_pass
ES_CA_PATH = settings.es_ca_path
ES_CLIENT_CERT = settings.es_client_cert
ES_CLIENT_KEY = settings.es_client_key
QUERY_HUB_USERNAME = settings.query_hub_username
QUERY_HUB_PASSWORD = settings.query_hub_password
SCROLL_TIMEOUT = settings.scroll_timeout
CHUNK_SIZE = settings.chunk_size
NUM_SLICES = settings.num_slices
ORG_NAME_FILTER = settings.org_name_filter
SEVERITY_FILTER = settings.severity_filter
