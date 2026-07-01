from fastapi import APIRouter

def get_all_ticket_routers() -> APIRouter:
    """Return a list of all API routers from the apps."""
    from .ticket import router as ticket_router
    from .activity_log import router as activity_log_router
    from .comment import router as comment_router
    from .attachment import router as attachment_router
    from .sla_policy import router as sla_policy_router
    from .task import router as task_router

    router = APIRouter(prefix="/api/v1")
    router.include_router(ticket_router)
    router.include_router(activity_log_router)
    router.include_router(comment_router)
    router.include_router(attachment_router)
    router.include_router(sla_policy_router)
    router.include_router(task_router)
    
    return router