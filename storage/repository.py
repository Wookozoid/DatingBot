"""
Слой доступа к данным, то что нужно для хранения анкеты.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from storage.models import User


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def create_user(session: AsyncSession, user_id: int, name: str, age: int) -> User:
    user = User(id=user_id, name=name, age=age)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user