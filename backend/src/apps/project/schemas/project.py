from src.core.enums import RBACRole
from src.core.types import  HashId
from src.core.schemas import BaseSchema


class ProjectCreateRequest(BaseSchema):
    name: str
    description: str | None = None