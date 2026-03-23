from fastapi import APIRouter

from .admin import router as admin_router
from .milestones import router as milestones_router
from .projects import router as projects_router
from .releases import router as releases_router
from .reports import router as reports_router
from .tickets import router as tickets_router

router = APIRouter()
router.include_router(tickets_router, tags=["flowtrack-tickets"])
router.include_router(projects_router, tags=["flowtrack-projects"])
router.include_router(milestones_router, tags=["flowtrack-milestones"])
router.include_router(releases_router, tags=["flowtrack-releases"])
router.include_router(reports_router, tags=["flowtrack-reports"])
router.include_router(admin_router, tags=["flowtrack-admin"])
