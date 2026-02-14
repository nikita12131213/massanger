import asyncio

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Conversation, Message, Participant, User
from app.utils.security import hash_password


async def main() -> None:
    async with SessionLocal() as db:
        users = {}
        for name in ["alice", "bob", "charlie"]:
            u = await db.scalar(select(User).where(User.username == name))
            if not u:
                u = User(username=name, password_hash=hash_password("password"))
                db.add(u)
                await db.flush()
            users[name] = u

        conv = Conversation(is_group=False)
        db.add(conv)
        await db.flush()
        db.add_all([
            Participant(conversation_id=conv.id, user_id=users["alice"].id),
            Participant(conversation_id=conv.id, user_id=users["bob"].id),
            Message(conversation_id=conv.id, sender_id=users["alice"].id, text="Привет, Bob!"),
            Message(conversation_id=conv.id, sender_id=users["bob"].id, text="Привет, Alice 👋"),
        ])
        await db.commit()
    print("Seed complete")


if __name__ == "__main__":
    asyncio.run(main())
