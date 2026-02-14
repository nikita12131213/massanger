from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RefreshToken, User
from app.utils.security import (
    USERNAME_RE,
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)


async def register_user(db: AsyncSession, username: str, password: str) -> User:
    if not USERNAME_RE.match(username):
        raise HTTPException(status_code=400, detail="Invalid username format")
    if await db.scalar(select(User).where(User.username == username)):
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(username=username, password_hash=hash_password(password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login_user(db: AsyncSession, username: str, password: str) -> tuple[str, str]:
    user = await db.scalar(select(User).where(User.username == username))
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access = create_access_token(user.id)
    refresh, exp = create_refresh_token(user.id)
    db.add(RefreshToken(user_id=user.id, token_hash=hash_token(refresh), expires_at=exp))
    await db.commit()
    return access, refresh


async def rotate_refresh(db: AsyncSession, token: str) -> tuple[int, str, str]:
    from app.utils.security import decode_token

    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = int(payload["sub"])
    token_hash = hash_token(token)
    current = await db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash, RefreshToken.revoked.is_(False))
    )
    if not current or current.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired")
    current.revoked = True
    access = create_access_token(user_id)
    new_refresh, exp = create_refresh_token(user_id)
    db.add(RefreshToken(user_id=user_id, token_hash=hash_token(new_refresh), expires_at=exp))
    await db.commit()
    return user_id, access, new_refresh


async def revoke_refresh(db: AsyncSession, token: str | None) -> None:
    if not token:
        return
    t_hash = hash_token(token)
    row = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == t_hash))
    if row:
        row.revoked = True
        await db.commit()
