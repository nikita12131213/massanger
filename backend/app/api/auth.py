from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.config import get_settings
from app.db.session import get_db
from app.schemas.auth import LoginIn, RegisterIn, TokenOut
from app.schemas.common import UserOut
from app.services.auth_service import login_user, register_user, revoke_refresh, rotate_refresh
from app.services.redis_client import redis
from app.utils.rate_limit import is_rate_limited

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def set_refresh_cookie(response: Response, refresh: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/",
        max_age=settings.refresh_token_expire_days * 86400,
    )


@router.post("/register", response_model=UserOut)
async def register(payload: RegisterIn, request: Request, db: AsyncSession = Depends(get_db)):
    ip = request.client.host if request.client else "anon"
    if await is_rate_limited(redis, f"rl:register:{ip}", settings.rate_limit_register):
        raise HTTPException(status_code=429, detail="Too many register attempts")
    user = await register_user(db, payload.username.lower(), payload.password)
    return UserOut(id=user.id, username=user.username)


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    ip = request.client.host if request.client else "anon"
    if await is_rate_limited(redis, f"rl:login:{ip}", settings.rate_limit_login):
        raise HTTPException(status_code=429, detail="Too many login attempts")
    access, refresh = await login_user(db, payload.username.lower(), payload.password)
    set_refresh_cookie(response, refresh)
    return TokenOut(access_token=access)


@router.post("/refresh", response_model=TokenOut)
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    _, access, refresh_token = await rotate_refresh(db, token)
    set_refresh_cookie(response, refresh_token)
    return TokenOut(access_token=access)


@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    await revoke_refresh(db, request.cookies.get("refresh_token"))
    response.delete_cookie("refresh_token", path="/")
    return {"ok": True}


@router.get("/me", response_model=UserOut)
async def me(user=Depends(get_current_user)):
    return UserOut(id=user.id, username=user.username)
