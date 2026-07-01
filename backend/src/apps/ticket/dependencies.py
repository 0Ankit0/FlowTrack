from typing import Annotated
from src.db.query import select
from src.core.exceptions import NotFoundError
from fastapi import Path, Depends
from src.apps.ticket.models.ticket import Ticket
from src.core.dependencies import DB, CurrentProject
from src.core.types import HashId


async def get_current_ticket(
    db: DB,
    current_project: CurrentProject,
    ticket_id: Annotated[HashId, Path(description="Ticket ID")],
) -> Ticket:
    """Fetches a specific ticket, ensuring it belongs completely to the resolved project scope."""
    query = select(Ticket).where(
        Ticket.id == ticket_id,
        Ticket.project_id == current_project.id
    )
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise NotFoundError(message="Ticket not found")
    return ticket

CurrentTicket = Annotated[Ticket, Depends(get_current_ticket)]
