from fastapi import APIRouter

from routers.aggregation_router import router as aggregation_router
from routers.auth_router import router as auth_router
from routers.search_router import router as search_router
from routers.write_router import router as write_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(search_router)
api_router.include_router(write_router)
api_router.include_router(aggregation_router)
