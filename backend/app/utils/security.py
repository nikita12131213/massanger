import hashlib
import re
from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,32}$")


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_ctx.verify(password, password_hash)


def create_access_token(user_id: int) -> str:
    exp = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(user_id), "type": "access", "exp": exp}, settings.secret_key, algorithm="HS256")


def create_refresh_token(user_id: int) -> tuple[str, datetime]:
    exp = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    token = jwt.encode({"sub": str(user_id), "type": "refresh", "exp": exp}, settings.secret_key, algorithm="HS256")
    return token, exp


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def sanitize_text(value: str) -> str:
    cleaned = value.strip().replace("\x00", "")
    return cleaned[:4000]
