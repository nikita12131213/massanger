from pydantic import BaseModel, Field


class CreateConversationIn(BaseModel):
    username: str = Field(min_length=3, max_length=32)


class SendMessageIn(BaseModel):
    conversation_id: int
    text: str = Field(min_length=1, max_length=4000)


class EditMessageIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
