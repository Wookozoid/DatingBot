"""
Просмотр анкет через /find.

Пока БЕЗ лайков/дизлайков и без ML-ранжирования.
"""
import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from storage.database import get_session
from storage.repository import get_user, get_candidates

logger = logging.getLogger(__name__)

router = Router(name="browsing")

CANDIDATES_LIMIT = 10


def _next_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Следующая анкета", callback_data="next_candidate")]]
    )


async def _show_candidate(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    queue: list[int] = data.get("browse_queue", [])
    index: int = data.get("browse_index", 0)

    if index >= len(queue):
        await message.answer("Анкеты закончились. Загляни чуть позже...")
        return

    async with get_session() as session:
        candidate = await get_user(session, queue[index])

    if candidate is None:
        await state.update_data(browse_index=index + 1)
        await _show_candidate(message, state)
        return

    caption = f"{candidate.name}, {candidate.age}\n{candidate.city}\n\n{candidate.bio_text}"
    await message.answer_photo(candidate.photo_file_id, caption=caption, reply_markup=_next_keyboard())


@router.message(Command("find"))
async def cmd_find(message: Message, state: FSMContext) -> None:
    async with get_session() as session:
        user = await get_user(session, message.from_user.id)
        if user is None:
            await message.answer("Сначала создай анкету: нажми /start")
            return
        candidates = await get_candidates(session, user, limit=CANDIDATES_LIMIT)

    logger.info("Пользователю %s подобрано %d кандидатов", message.from_user.id, len(candidates))

    await state.update_data(browse_queue=[c.id for c in candidates], browse_index=0)

    if not candidates:
        await message.answer("Пока нет подходящих анкет. Попробуй позже.")
        return

    await _show_candidate(message, state)


@router.callback_query(F.data == "next_candidate")
async def process_next(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    await state.update_data(browse_index=data.get("browse_index", 0) + 1)
    await _show_candidate(callback.message, state)