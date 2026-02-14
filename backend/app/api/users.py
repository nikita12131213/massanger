from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.common import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/search", response_model=list[UserOut])
async def search_users(
    q: str = Query(min_length=1, max_length=32),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    rows = (
        await db.scalars(select(User).where(User.username.ilike(f"%{q.lower()}%"), User.id != user.id).limit(20))
    ).all()
    return [UserOut(id=x.id, username=x.username) for x in rows]
