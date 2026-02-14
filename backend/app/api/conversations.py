from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.schemas.common import ConversationOut, MessageOut, UserOut
from app.schemas.messages import CreateConversationIn
from app.services.conversation_service import (
    check_participant,
    create_or_get_private_conversation,
    get_last_message,
    get_peer,
    get_unread_count,
    list_conversations,

)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationOut])
async def get_conversations(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    items = []
    for c in await list_conversations(db, user.id):
        peer = await get_peer(db, c.id, user.id)
        last = await get_last_message(db, c.id)
        unread = await get_unread_count(db, c.id, user.id)
        items.append(
            ConversationOut(
                id=c.id,
                peer=UserOut(id=peer.id, username=peer.username) if peer else None,
                last_message=(
                    MessageOut(
                        id=last.id,
                        conversation_id=last.conversation_id,
                        sender_id=last.sender_id,
                        text=last.text,
                        created_at=last.created_at,
                        edited_at=last.edited_at,
                        attachments=[],
                    )
                    if last
                    else None
                ),
                unread_count=unread,
            )
        )
    return items


@router.post("", response_model=ConversationOut)
async def create_conversation(payload: CreateConversationIn, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    try:
        conv = await create_or_get_private_conversation(db, user.id, payload.username.lower())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    peer = await get_peer(db, conv.id, user.id)
    return ConversationOut(id=conv.id, peer=UserOut(id=peer.id, username=peer.username), unread_count=0)


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if not await check_participant(db, user.id, conversation_id):
        raise HTTPException(status_code=403, detail="No access")
    peer = await get_peer(db, conversation_id, user.id)
    return {
        "id": conversation_id,
        "participants": [
            {"id": user.id, "username": user.username},
            {"id": peer.id, "username": peer.username} if peer else None,
        ],
    }

