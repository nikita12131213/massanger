from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation, Message, Participant, User


async def create_or_get_private_conversation(db: AsyncSession, my_id: int, username: str) -> Conversation:
    peer = await db.scalar(select(User).where(User.username == username))
    if not peer or peer.id == my_id:
        raise ValueError("Invalid peer")

    subquery = (
        select(Participant.conversation_id)
        .where(Participant.user_id.in_([my_id, peer.id]))
        .group_by(Participant.conversation_id)
        .having(func.count(Participant.user_id) == 2)
    )
    existing = await db.scalar(select(Conversation).where(Conversation.id.in_(subquery), Conversation.is_group.is_(False)))
    if existing:
        return existing

    conv = Conversation(is_group=False)
    db.add(conv)
    await db.flush()
    db.add_all([
        Participant(conversation_id=conv.id, user_id=my_id),
        Participant(conversation_id=conv.id, user_id=peer.id),
    ])
    await db.commit()
    await db.refresh(conv)
    return conv


async def check_participant(db: AsyncSession, user_id: int, conversation_id: int) -> bool:
    row = await db.scalar(
        select(Participant.id).where(
            Participant.user_id == user_id,
            Participant.conversation_id == conversation_id,
        )
    )
    return bool(row)


async def list_conversations(db: AsyncSession, user_id: int):
    stmt = (
        select(Conversation)
        .join(Participant, Participant.conversation_id == Conversation.id)
        .where(Participant.user_id == user_id)
        .order_by(Conversation.id.desc())
    )
    return (await db.scalars(stmt)).all()


async def get_peer(db: AsyncSession, conversation_id: int, my_id: int):
    stmt = (
        select(User)
        .join(Participant, Participant.user_id == User.id)
        .where(Participant.conversation_id == conversation_id, User.id != my_id)
    )
    return await db.scalar(stmt)


async def get_last_message(db: AsyncSession, conversation_id: int):
    return await db.scalar(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id.desc())
    )


async def get_unread_count(db: AsyncSession, conversation_id: int, user_id: int) -> int:
    p = await db.scalar(
        select(Participant).where(Participant.conversation_id == conversation_id, Participant.user_id == user_id)
    )
    if not p:
        return 0
    cond = [Message.conversation_id == conversation_id, Message.sender_id != user_id]
    if p.last_read_message_id:
        cond.append(Message.id > p.last_read_message_id)
    return (await db.scalar(select(func.count(Message.id)).where(and_(*cond)))) or 0
