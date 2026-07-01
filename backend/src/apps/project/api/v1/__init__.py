from fastapi import APIRouter

from .project import router as project_router
from .milestone import router as milestone_router

def get_all_project_routers() -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    router.include_router(project_router)
    router.include_router(milestone_router)
    return router