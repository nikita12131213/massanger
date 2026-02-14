import asyncio
import json
from collections import defaultdict

from fastapi import WebSocket

from app.services.redis_client import redis


class WSManager:
    def __init__(self) -> None:
        self.connections: dict[int, list[WebSocket]] = defaultdict(list)
        self.started = False

    async def connect(self, user_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self.connections[user_id].append(ws)

    async def disconnect(self, user_id: int, ws: WebSocket) -> None:
        if ws in self.connections.get(user_id, []):
            self.connections[user_id].remove(ws)

    async def send_user(self, user_id: int, event: str, payload: dict) -> None:
        for ws in self.connections.get(user_id, []):
            await ws.send_json({"event": event, "payload": payload})

    async def publish_conversation(self, conversation_id: int, event: str, payload: dict) -> None:
        await redis.publish(f"conv:{conversation_id}", json.dumps({"event": event, "payload": payload}))

    async def start_pubsub(self) -> None:
        if self.started:
            return
        self.started = True
        asyncio.create_task(self._run_pubsub())

    async def _run_pubsub(self) -> None:
        pubsub = redis.pubsub()
        await pubsub.psubscribe("conv:*")
        async for msg in pubsub.listen():
            if msg.get("type") not in {"pmessage"}:
                continue
            data = json.loads(msg["data"])
            payload = data["payload"]
            for uid in payload.get("participant_ids", []):
                await self.send_user(uid, data["event"], payload)


manager = WSManager()
