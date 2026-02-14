from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.config import get_settings
from app.db.session import get_db
from app.schemas.common import AttachmentOut, MessageOut
from app.schemas.messages import EditMessageIn, SendMessageIn
from app.services.conversation_service import check_participant
from app.services.message_service import create_message, edit_message, list_messages, search_messages, soft_delete_for_me
from app.services.redis_client import redis
from app.utils.rate_limit import is_rate_limited

router = APIRouter(prefix="/messages", tags=["messages"])
settings = get_settings()


def _to_message_out(msg) -> MessageOut:
    return MessageOut(
        id=msg.id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        text=msg.text,
        created_at=msg.created_at,
        edited_at=msg.edited_at,
        attachments=[AttachmentOut(id=a.id, url=a.url, kind=a.kind, mime=a.mime, size=a.size) for a in msg.attachments],
    )


@router.get("", response_model=list[MessageOut])
async def get_messages(
    conversation_id: int,
    before: int | None = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if not await check_participant(db, user.id, conversation_id):
        raise HTTPException(status_code=403, detail="No access")
    return [_to_message_out(x) for x in await list_messages(db, conversation_id, user.id, before, limit)]


@router.post("", response_model=MessageOut)
async def send_message(payload: SendMessageIn, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if not await check_participant(db, user.id, payload.conversation_id):
        raise HTTPException(status_code=403, detail="No access")
    if await is_rate_limited(redis, f"rl:msg:{user.id}", settings.rate_limit_message):
        raise HTTPException(status_code=429, detail="Too many messages")
    return _to_message_out(await create_message(db, payload.conversation_id, user.id, payload.text))


@router.patch("/{message_id}", response_model=MessageOut)
async def patch_message(message_id: int, payload: EditMessageIn, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return _to_message_out(await edit_message(db, message_id, user.id, payload.text))


@router.delete("/{message_id}")
async def delete_message(message_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await soft_delete_for_me(db, message_id, user.id)
    return {"ok": True}


@router.get("/search", response_model=list[MessageOut])
async def search(
    conversation_id: int,
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if not await check_participant(db, user.id, conversation_id):
        raise HTTPException(status_code=403, detail="No access")
    return [_to_message_out(x) for x in await search_messages(db, conversation_id, user.id, q, limit)]
