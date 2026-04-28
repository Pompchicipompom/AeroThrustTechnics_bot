from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attachment import Attachment


async def create_attachments(session: AsyncSession, attachments: list[Attachment]) -> None:
    session.add_all(attachments)
    await session.flush()
