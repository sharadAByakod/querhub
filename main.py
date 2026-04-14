import logging
from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response

from config.settings import LOG_LEVEL
from database.elasticsearch.elastic import connect_elasticsearch, get_es
from routers.view_router import router as view_router
from routers.aggregation_router import router as aggregation_router
from utils.support import rate_limit

app = FastAPI(
    title="QueryHub Application",
    description="""
QueryHub is a high-performance FastAPI service that provides a secure, view-based interface for Elasticsearch.

### Key Features:
* **View-Based Search**: Query data using simplified, flat field aliases.
* **Controlled Writes**: Validate and update documents using model-defined allowlists.
* **Security**: Integrated Bearer token authentication and view-level authorization.
* **Pagination**: Supports both standard from/size and high-performance PIT-based pagination.
""",
    version="2.0.0",
    contact={
        "name": "QueryHub Support",
        "url": "https://github.com/sharadAByakod/querhub",
    },
    docs_url="/docs",
    redoc_url="/redoc",
)

numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)

logging.basicConfig(level=numeric_level)


@app.on_event("startup")
async def startup_event() -> None:
    connect_elasticsearch()
    print("Elasticsearch started")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    es = get_es()
    if es:
        es.close()
        print("Elasticsearch closed")


@app.middleware("http")
async def rate_limit_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    client_ip = request.client.host if request.client else "unknown"
    rate_limit(client_ip)

    response = await call_next(request)
    return response


Prefix_str = "/api/v2"

app.include_router(view_router, prefix=Prefix_str)
app.include_router(aggregation_router, prefix=Prefix_str)

# =================================
# SERVER RUNNER
# =================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
    )
