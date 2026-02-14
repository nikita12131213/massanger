from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Attachment, Message, MessageDelete
from app.utils.security import sanitize_text


async def create_message(db: AsyncSession, conversation_id: int, sender_id: int, text: str) -> Message:
    msg = Message(conversation_id=conversation_id, sender_id=sender_id, text=sanitize_text(text))
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def list_messages(db: AsyncSession, conversation_id: int, user_id: int, before: int | None, limit: int):
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .options(selectinload(Message.attachments))
        .order_by(desc(Message.id))
        .limit(limit)
    )
    if before:
        stmt = stmt.where(Message.id < before)

    rows = (await db.scalars(stmt)).all()
    deleted_ids = set(
        (
            await db.scalars(
                select(MessageDelete.message_id).where(
                    MessageDelete.user_id == user_id, MessageDelete.message_id.in_([m.id for m in rows] or [0])
                )
            )
        ).all()
    )
    return [m for m in rows if m.id not in deleted_ids]


async def edit_message(db: AsyncSession, message_id: int, user_id: int, text: str) -> Message:
    msg = await db.scalar(select(Message).where(Message.id == message_id))
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.sender_id != user_id:
        raise HTTPException(status_code=403, detail="No access")
    msg.text = sanitize_text(text)
    msg.edited_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(msg)
    return msg


async def soft_delete_for_me(db: AsyncSession, message_id: int, user_id: int) -> None:
    exists = await db.scalar(
        select(MessageDelete).where(MessageDelete.message_id == message_id, MessageDelete.user_id == user_id)
    )
    if exists:
        return
    db.add(MessageDelete(message_id=message_id, user_id=user_id))
    await db.commit()


async def search_messages(db: AsyncSession, conversation_id: int, user_id: int, q: str, limit: int):
    stmt = (
        select(Message)
        .where(and_(Message.conversation_id == conversation_id, Message.text.ilike(f"%{q}%")))
        .order_by(desc(Message.id))
        .limit(limit)
    )
    rows = (await db.scalars(stmt)).all()
    deleted = set(
        (
            await db.scalars(
                select(MessageDelete.message_id).where(
                    MessageDelete.user_id == user_id, MessageDelete.message_id.in_([m.id for m in rows] or [0])
                )
            )
        ).all()
    )
    return [m for m in rows if m.id not in deleted]


async def add_attachment(
    db: AsyncSession,
    message_id: int,
    url: str,
    mime: str,
    size: int,
    width: int | None = None,
    height: int | None = None,
) -> Attachment:
    a = Attachment(message_id=message_id, kind="image", url=url, mime=mime, size=size, width=width, height=height)
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return a
