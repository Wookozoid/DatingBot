"""
/matches показывает список взаимных совпадений пользователя.
"""
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from storage.database import get_session
from storage.repository import get_matches

logger = logging.getLogger(__name__)

router = Router(name="matches")


@router.message(Command("matches"))
async def cmd_matches(message: Message) -> None:
    async with get_session() as session:
        matches = await get_matches(session, message.from_user.id)

    if not matches:
        await message.answer("Пока нет совпадений. Смотри анкеты в /find")
        return

    await message.answer(f"У тебя {len(matches)} совпадений:")
    for user in matches:
        caption = f"{user.name}, {user.age}\n{user.city}"
        await message.answer_photo(user.photo_file_id, caption=caption)