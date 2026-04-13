import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_USER = os.getenv("ES_USER", "elastic")
ES_PASS = os.getenv("ES_PASS", "abc")
ES_CA_PATH: str = os.getenv("ES_CA_PATH", "ca.crt")
ES_CLIENT_CERT: str = os.getenv("ES_CLIENT_CERT", "client.crt")
ES_CLIENT_KEY: str = os.getenv("ES_CLIENT_KEY", "client.key")

QUERY_HUB_USERNAME = os.getenv("QUERY_HUB_USERNAME", "asi_query_hub")
QUERY_HUB_PASSWORD = os.getenv("QUERY_HUB_PASSWORD")

SCROLL_TIMEOUT = os.getenv("SCROLL_TIMEOUT", "2m")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
NUM_SLICES = int(os.getenv("NUM_SLICES", 2))

ORG_NAME_FILTER = (
    "BT Security - IMPSS Management Systems - Reigate",
    "BT Security - IMPSS Management Systems - Derby",
)

SEVERITY_FILTER = os.getenv("SEVERITY_FILTER", "HIGH,CRITICAL").split(",")
