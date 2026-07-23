"""
Регистрация пользователя:
спрашиваем, а потом сохраняем в БД.
"""
import logging

from aiogram import Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from storage.database import get_session
from storage.repository import get_user, create_user

logger = logging.getLogger(__name__)

router = Router(name="onboarding")


class Onboarding(StatesGroup):
    name = State()
    age = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    async with get_session() as session:
        existing = await get_user(session, message.from_user.id)

    if existing:
        await message.answer(f"С возвращением, {existing.name}! Анкета уже сохранена.")
        return

    logger.info("Пользователь %s начал регистрацию", message.from_user.id)
    await state.set_state(Onboarding.name)
    await message.answer("Привет! Давай создадим анкету.\nКак тебя зовут?")


@router.message(StateFilter(Onboarding.name))
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await state.set_state(Onboarding.age)
    await message.answer("Сколько тебе лет?")


@router.message(StateFilter(Onboarding.age))
async def process_age(message: Message, state: FSMContext) -> None:
    if not message.text.isdigit() or not (0 <= int(message.text) <= 99):
        await message.answer("Введи возраст числом от 0 до 99")
        return

    data = await state.update_data(age=int(message.text))
    await state.clear()

    async with get_session() as session:
        await create_user(session, user_id=message.from_user.id, name=data["name"], age=data["age"])


    logger.info("Пользователь %s зарегистрирован", message.from_user.id)
    await message.answer(f"Готово, мы все сделали, {data['name']}!")
