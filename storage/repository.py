"""
Слой доступа к данным, то что нужно для хранения анкеты.
"""
import json

from sqlalchemy import select, not_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from storage.models import User, Gender, Interaction, InteractionType, Match


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


async def get_candidates(session: AsyncSession, user: User) -> list[User]:
    """
    Подбор всех подходящих по полу/предпочтениям кандидатов с эмбеддингом,
    ИСКЛЮЧАЯ тех, кого пользователь уже лайкнул/дизлайкнул
    """
    already_interacted_subq = select(Interaction.to_user_id).where(
        Interaction.from_user_id == user.id
    )
    query = select(User).where(
        User.id != user.id,
        User.gender == user.looking_for,
        User.looking_for == user.gender,
        User.embedding.is_not(None),
        not_(User.id.in_(already_interacted_subq)),
    )
    result = await session.execute(query)
    return list(result.scalars().all())


async def delete_user(session: AsyncSession, user_id: int) -> bool:
    """
    Удаляет анкету пользователя.
    Возвращает True, если анкета была и удалена.
    """
    user = await session.get(User, user_id)
    if user is None:
        return False
    await session.delete(user)
    await session.commit()
    return True


async def record_interaction(
    session: AsyncSession,
    from_user_id: int,
    to_user_id: int,
    interaction_type: InteractionType,
) -> Match | None:
    """
    Лайк/дизлайк. Если это лайк и он оказался взаимным -
    создает запись в Match и возвращает ее
    """
    existing = await session.execute(
        select(Interaction).where(
            Interaction.from_user_id == from_user_id,
            Interaction.to_user_id == to_user_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return None

    session.add(Interaction(from_user_id=from_user_id, to_user_id=to_user_id, type=interaction_type))
    await session.commit()

    if interaction_type != InteractionType.LIKE:
        return None

    reverse_like = await session.execute(
        select(Interaction).where(
            Interaction.from_user_id == to_user_id,
            Interaction.to_user_id == from_user_id,
            Interaction.type == InteractionType.LIKE,
        )
    )
    if reverse_like.scalar_one_or_none() is None:
        return None

    user_a_id, user_b_id = sorted([from_user_id, to_user_id])
    match = Match(user_a_id=user_a_id, user_b_id=user_b_id)
    session.add(match)
    await session.commit()
    await session.refresh(match)
    return match


async def get_matches(session: AsyncSession, user_id: int) -> list[User]:
    """
    Возвращает анкеты всех, с кем у пользователя взаимный мэтч.
    """
    result = await session.execute(
        select(Match).where(or_(Match.user_a_id == user_id, Match.user_b_id == user_id))
    )
    matches = result.scalars().all()
    other_ids = [m.user_b_id if m.user_a_id == user_id else m.user_a_id for m in matches]
    if not other_ids:
        return []

    users_result = await session.execute(select(User).where(User.id.in_(other_ids)))
    return list(users_result.scalars().all())


async def get_users_who_liked_me(session: AsyncSession, user_id: int) -> list[User]:
    """
    Просмотр анкет, котоыре поставили лайк пользователю
    """
    liked_me_subq = select(Interaction.from_user_id).where(
        Interaction.to_user_id == user_id, Interaction.type == InteractionType.LIKE
    )

    already_responded_subq = select(Interaction.to_user_id).where(
        Interaction.from_user_id == user_id
    )

    query = select(User).where(
        User.id.in_(liked_me_subq),
        not_(User.id.in_(already_responded_subq)),
    )
    
    result = await session.execute(query)
    return list(result.scalars().all())
