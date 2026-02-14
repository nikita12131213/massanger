from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.realtime.manager import manager
from sqlalchemy import select

from app.models import Participant
from app.services.conversation_service import check_participant
from app.services.message_service import create_message
from app.services.redis_client import redis
from app.utils.rate_limit import clear_typing, mark_typing
from app.utils.security import decode_token

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=1008)
        return
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except Exception:
        await ws.close(code=1008)
        return

    await manager.connect(user_id, ws)
    await manager.start_pubsub()
    await redis.set(f"presence:{user_id}", "online", ex=120)
    try:
        while True:
            data = await ws.receive_json()
            event = data.get("event")
            p = data.get("payload", {})
            async with SessionLocal() as db:
                if event == "message:send":
                    conv_id = int(p["conversation_id"])
                    if not await check_participant(db, user_id, conv_id):
                        await ws.send_json({"event": "error", "payload": {"message": "No access"}})
                        continue
                    msg = await create_message(db, conv_id, user_id, p.get("text", ""))
                    ids = (await db.scalars(select(Participant.user_id).where(Participant.conversation_id == conv_id))).all()
                    await ws.send_json(
                        {
                            "event": "message:ack",
                            "payload": {"temp_id": p.get("temp_id"), "message_id": msg.id, "created_at": msg.created_at.isoformat()},
                        }
                    )
                    await manager.publish_conversation(
                        conv_id,
                        "message:new",
                        {
                            "participant_ids": ids,
                            "message": {
                                "id": msg.id,
                                "conversation_id": conv_id,
                                "sender_id": user_id,
                                "text": msg.text,
                                "created_at": msg.created_at.isoformat(),
                                "attachments": [],
                            },
                        },
                    )
                elif event == "typing:start":
                    conv_id = int(p["conversation_id"])
                    await mark_typing(redis, conv_id, user_id)
                    ids = (await db.scalars(select(Participant.user_id).where(Participant.conversation_id == conv_id))).all()
                    await manager.publish_conversation(
                        conv_id,
                        "typing:start",
                        {"participant_ids": ids, "conversation_id": conv_id, "user_id": user_id},
                    )
                elif event == "typing:stop":
                    conv_id = int(p["conversation_id"])
                    await clear_typing(redis, conv_id, user_id)
                    ids = (await db.scalars(select(Participant.user_id).where(Participant.conversation_id == conv_id))).all()
                    await manager.publish_conversation(
                        conv_id,
                        "typing:stop",
                        {"participant_ids": ids, "conversation_id": conv_id, "user_id": user_id},
                    )
    except WebSocketDisconnect:
        await manager.disconnect(user_id, ws)
        await redis.set(f"presence:{user_id}", "offline", ex=120)
