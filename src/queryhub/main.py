from contextlib import asynccontextmanager
import logging
from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response

from queryhub.config.settings import settings
from queryhub.database.elasticsearch.elastic import connect_elasticsearch, get_es
from queryhub.routers.api_router import api_router
from queryhub.utils.support import rate_limit

logger = logging.getLogger(__name__)
API_PREFIX = "/api/v2"

numeric_level = getattr(logging, settings.log_level, logging.INFO)

logging.basicConfig(level=numeric_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    connect_elasticsearch()
    logger.info("Elasticsearch started")
    try:
        yield
    finally:
        es = get_es()
        if es:
            es.close()
            logger.info("Elasticsearch closed")


async def rate_limit_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    client_ip = request.client.host if request.client else "unknown"
    rate_limit(client_ip)

    response = await call_next(request)
    return response


def create_app() -> FastAPI:
    app = FastAPI(
        title="QueryHub Application",
        description=(
            "QueryHub is a high-performance FastAPI service that provides a secure, "
            "view-based interface for Elasticsearch.\n\n"
            "### Key Features:\n"
            "* **View-Based Search**: Query data using simplified, flat field aliases.\n"
            "* **Controlled Writes**: Validate and update documents using model-defined "
            "allowlists.\n"
            "* **Security**: Integrated Bearer token authentication and view-level "
            "authorization.\n"
            "* **Pagination**: Supports both standard from/size and high-performance "
            "PIT-based pagination.\n"
        ),
        version="2.0.0",
        contact={
            "name": "QueryHub Support",
            "url": "https://github.com/sharadAByakod/querhub",
        },
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.middleware("http")(rate_limit_middleware)
    app.include_router(api_router, prefix=API_PREFIX)
    return app


app = create_app()

# =================================
# SERVER RUNNER
# =================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "queryhub.main:app",
        host="0.0.0.0",
        port=8001,
    )
