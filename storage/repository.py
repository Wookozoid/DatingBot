"""
Слой доступа к данным, то что нужно для хранения анкеты.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from storage.models import User, Gender


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def create_user(
    session: AsyncSession,
    user_id: int,
    name: str,
    age: int,
    gender: Gender,
    looking_for: Gender,
    city: str,
    bio_text: str,
    photo_file_id: str,
) -> User:
    user = User(
        id=user_id,
        name=name,
        age=age,
        gender=gender,
        looking_for=looking_for,
        city=city,
        bio_text=bio_text,
        photo_file_id=photo_file_id,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
