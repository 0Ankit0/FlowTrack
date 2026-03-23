from fastapi import APIRouter

from .v1 import router as v1_router

flowtrack_router = APIRouter()
flowtrack_router.include_router(v1_router)

__all__ = ["flowtrack_router"]
