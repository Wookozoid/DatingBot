"""
Ответ на сообщение, к-ое не подходит ни под одни хендлер
"""
from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.types import Message

router = Router(name="fallback")

HELP_TEXT = (
    "Вот что я умею:\n\n"
    "/start — что это за бот\n"
    "/create — создать анкету (если её ещё нет)\n"
    "/find — смотреть анкеты и лайкать\n"
    "/likes — посмотреть, кто лайкнул тебя\n"
    "/matches — твои взаимные совпадения\n"
    "/me — посмотреть свою анкету\n"
    "/edit_bio — изменить текст анкеты\n"
    "/delete — удалить анкету"
)


@router.message(StateFilter(None))
async def fallback_handler(message: Message) -> None:
    await message.answer(HELP_TEXT)