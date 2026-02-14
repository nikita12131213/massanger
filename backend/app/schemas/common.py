from datetime import datetime

from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    username: str


class AttachmentOut(BaseModel):
    id: int
    url: str
    kind: str
    mime: str
    size: int


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    text: str
    created_at: datetime
    edited_at: datetime | None = None
    attachments: list[AttachmentOut] = []


class ConversationOut(BaseModel):
    id: int
    peer: UserOut | None
    last_message: MessageOut | None = None
    unread_count: int = 0
