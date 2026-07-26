"""
Просмотр анкет через /find (по ранжированию) и /likes (кто лайкнул тебя).

Теперь есть лайк/дизлайк/пропуск.
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

from bot.services.ranking import rank_candidates
from storage.database import get_session
from storage.models import InteractionType
from storage.repository import get_user, get_candidates, get_users_who_liked_me, record_interaction

logger = logging.getLogger(__name__)

router = Router(name="browsing")


def _actions_keyboard(candidate_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👎", callback_data=f"react:dislike:{candidate_id}"),
                InlineKeyboardButton(text="⏭", callback_data=f"react:skip:{candidate_id}"),
                InlineKeyboardButton(text="❤️", callback_data=f"react:like:{candidate_id}"),
            ]
        ]
    )


async def _show_candidate(message: Message, state: FSMContext, empty_text: str) -> None:
    data = await state.get_data()
    queue: list[int] = data.get("browse_queue", [])
    index: int = data.get("browse_index", 0)

    if index >= len(queue):
        await message.answer(empty_text)
        return

    async with get_session() as session:
        candidate = await get_user(session, queue[index])

    if candidate is None:
        await state.update_data(browse_index=index + 1)
        await _show_candidate(message, state, empty_text)
        return

    caption = f"{candidate.name}, {candidate.age}\n{candidate.city}\n\n{candidate.bio_text}"
    await message.answer_photo(
        candidate.photo_file_id, caption=caption, reply_markup=_actions_keyboard(candidate.id)
    )


@router.message(Command("find"))
async def cmd_find(message: Message, state: FSMContext) -> None:
    async with get_session() as session:
        user = await get_user(session, message.from_user.id)
        if user is None:
            await message.answer("Сначала создай анкету: нажми /create")
            return
        all_candidates = await get_candidates(session, user)

    candidates = rank_candidates(user, all_candidates)
    logger.info("Пользователю %s подобрано %d кандидатов", message.from_user.id, len(candidates))

    await state.update_data(browse_queue=[c.id for c in candidates], browse_index=0, browse_mode="find")

    if not candidates:
        await message.answer("Пока нет подходящих анкет. Попробуй позже.")
        return

    await _show_candidate(message, state, "Анкеты закончились. Загляни чуть позже.")


@router.message(Command("likes"))
async def cmd_likes(message: Message, state: FSMContext) -> None:
    async with get_session() as session:
        user = await get_user(session, message.from_user.id)
        if user is None:
            await message.answer("Сначала создай анкету: нажми /create")
            return
        likers = await get_users_who_liked_me(session, user.id)

    await state.update_data(browse_queue=[u.id for u in likers], browse_index=0, browse_mode="likes")

    if not likers:
        await message.answer("Пока никто не лайкнул тебя. Загляни в /find, чтобы тебя увидели другие.")
        return

    await message.answer(f"Тебя лайкнули {len(likers)} человек. Смотрим?")
    await _show_candidate(message, state, "Это все, кто тебя лайкнул на текущий момент.")


async def _notify_match(callback: CallbackQuery, candidate_id: int) -> None:
    """
    Уведомляет обоих и обмениваемся контактами при мэтче
    """
    liker_username = f"@{callback.from_user.username}" if callback.from_user.username else "юзернейм не указан"

    try:
        candidate_chat = await callback.bot.get_chat(candidate_id)
        candidate_username = f"@{candidate_chat.username}" if candidate_chat.username else "юзернейм не указан"
    except Exception:
        candidate_username = "юзернейм не указан"

    await callback.message.answer(f"Это взаимно! Юз: {candidate_username}")
    await callback.bot.send_message(
        candidate_id,
        f"У тебя новый мэтч с {callback.from_user.first_name}! Юз: {liker_username}",
    )


@router.callback_query(F.data.startswith("react:"))
async def process_reaction(callback: CallbackQuery, state: FSMContext) -> None:
    _, action, candidate_id_str = callback.data.split(":")
    candidate_id = int(candidate_id_str)

    match = None
    if action in ("like", "dislike"):
        interaction_type = InteractionType.LIKE if action == "like" else InteractionType.DISLIKE
        async with get_session() as session:
            match = await record_interaction(session, callback.from_user.id, candidate_id, interaction_type)

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    if match:
        logger.info("Новый мэтч: %s <-> %s", match.user_a_id, match.user_b_id)
        await _notify_match(callback, candidate_id)
    elif action == "like":
        await callback.bot.send_message(candidate_id, "Тебя лайкнули! Для просмотра напиши /likes")

    data = await state.get_data()
    mode = data.get("browse_mode", "find")
    empty_text = (
        "Это все, кто тебя лайкнул на текущий момент."
        if mode == "likes"
        else "Анкеты закончились :("
    )
    await state.update_data(browse_index=data.get("browse_index", 0) + 1)
    await _show_candidate(callback.message, state, empty_text)