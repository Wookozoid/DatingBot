"""
/me посмотреть свою анкету
/edit_bio редактирование текста био (с пересчетом эмбеддинга)
/delete удаление своей анкеты. С подтверждением через кнопки
"""
import logging

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.services.embedding import get_embedding_service
from storage.database import get_session
from storage.repository import get_user, delete_user, update_bio

logger = logging.getLogger(__name__)

router = Router(name="profile")


class EditBio(StatesGroup):
    waiting_text = State()


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


@router.message(Command("edit_bio"))
async def cmd_edit_bio(message: Message, state: FSMContext) -> None:
    async with get_session() as session:
        user = await get_user(session, message.from_user.id)

    if user is None:
        await message.answer("У тебя еще нет анкеты. Нажми /create, чтобы создать.")
        return

    await state.set_state(EditBio.waiting_text)
    await message.answer(f"Текущее био:\n{user.bio_text}\n\nНапиши новый текст:")


@router.message(StateFilter(EditBio.waiting_text))
async def process_new_bio(message: Message, state: FSMContext) -> None:
    new_bio = message.text.strip()

    embedding_service = get_embedding_service()
    embedding = embedding_service.encode(new_bio)

    async with get_session() as session:
        await update_bio(session, message.from_user.id, new_bio, embedding)

    await state.clear()
    logger.info("Пользователь %s обновил био", message.from_user.id)
    await message.answer("Био обновлено!")


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
