"""
Слой доступа к данным, то что нужно для хранения анкеты.
"""
import json

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
    embedding: list[float] | None = None,
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
        embedding=json.dumps(embedding) if embedding is not None else None,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


def get_embedding(user: User) -> list[float] | None:
    """
    Достает эмбеддинг пользователя как обычный список float,
    а не JSON-строку.
    """
    if user.embedding is None:
        return None
    return json.loads(user.embedding)
