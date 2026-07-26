"""
/me посмотреть свою анкету
/delete удаление своей анкеты. С подтверждением через кнопки
"""
import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from storage.database import get_session
from storage.repository import get_user, delete_user

logger = logging.getLogger(__name__)

router = Router(name="profile")


def _confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, удалить", callback_data="delete_confirm"),
                InlineKeyboardButton(text="Отмена", callback_data="delete_cancel"),
            ]
        ]
    )


@router.message(Command("delete"))
async def cmd_delete(message: Message) -> None:
    async with get_session() as session:
        user = await get_user(session, message.from_user.id)

    if user is None:
        await message.answer("У тебя ещё нет анкеты, тебе нечего удалять.")
        return

    await message.answer(
        "Точно удалить твою анкету? Это действие необратимо.",
        reply_markup=_confirm_keyboard(),
    )


@router.message(Command("me"))
async def cmd_me(message: Message) -> None:
    async with get_session() as session:
        user = await get_user(session, message.from_user.id)

    if user is None:
        await message.answer("У тебя еще нет анкеты. Нажми /create, чтобы создать.")
        return

    caption = f"{user.name}, {user.age}\n{user.city}\n\n{user.bio_text}"
    await message.answer_photo(user.photo_file_id, caption=caption)


@router.callback_query(F.data == "delete_confirm")
async def process_delete_confirm(callback: CallbackQuery) -> None:
    async with get_session() as session:
        deleted = await delete_user(session, callback.from_user.id)

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    if deleted:
        logger.info("Пользователь %s удалил анкету", callback.from_user.id)
        await callback.message.answer("Анкета удалена. Захочешь вернуться - просто напиши /create")
    else:
        await callback.message.answer("Анкеты не найдено... Похоже ты уже ее удалял.")


@router.callback_query(F.data == "delete_cancel")
async def process_delete_cancel(callback: CallbackQuery) -> None:
    await callback.answer("Отменено")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Хорошо, анкета осталась на месте")
