"""
Регистрация пользователя:
спрашиваем, а потом сохраняем в БД.
"""
import logging

from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from storage.database import get_session
from storage.models import Gender
from storage.repository import get_user, create_user

from bot.services.embedding import get_embedding_service

logger = logging.getLogger(__name__)

router = Router(name="onboarding")


class Onboarding(StatesGroup):
    name = State()
    age = State()
    gender = State()
    looking_for = State()
    city = State()
    bio = State()
    photo = State()


_GENDER_MAP = {"Мужской": Gender.MALE, "Женский": Gender.FEMALE}


def _gender_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Мужской"), KeyboardButton(text="Женский")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    async with get_session() as session:
        existing = await get_user(session, message.from_user.id)

    if existing:
        logger.debug("Пользователь %s уже зарегистрирован", message.from_user.id)
        await message.answer(f"С возвращением, {existing.name}!")
        return

    logger.info("Пользователь %s начал регистрацию", message.from_user.id)
    await state.set_state(Onboarding.name)
    await message.answer(
        "Привет! Давай создадим анкету\nКак тебя зовут?",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(StateFilter(Onboarding.name))
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await state.set_state(Onboarding.age)
    await message.answer("Сколько тебе лет?")


@router.message(StateFilter(Onboarding.age))
async def process_age(message: Message, state: FSMContext) -> None:
    if not message.text.isdigit() or not (16 <= int(message.text) <= 99):
        await message.answer("Введи возраст числом от 16 до 99")
        return

    await state.update_data(age=int(message.text))
    await state.set_state(Onboarding.gender)
    await message.answer("Твой пол?", reply_markup=_gender_keyboard())


@router.message(StateFilter(Onboarding.gender), F.text.in_(_GENDER_MAP.keys()))
async def process_gender(message: Message, state: FSMContext) -> None:
    await state.update_data(gender=_GENDER_MAP[message.text])
    await state.set_state(Onboarding.looking_for)
    await message.answer("Кого ищем?", reply_markup=_gender_keyboard())


@router.message(StateFilter(Onboarding.gender))
async def process_gender_invalid(message: Message) -> None:
    await message.answer("Выбери вариант на клавиатуре ниже", reply_markup=_gender_keyboard())


@router.message(StateFilter(Onboarding.looking_for), F.text.in_(_GENDER_MAP.keys()))
async def process_looking_for(message: Message, state: FSMContext) -> None:
    await state.update_data(looking_for=_GENDER_MAP[message.text])
    await state.set_state(Onboarding.city)
    await message.answer("Из какого ты города?", reply_markup=ReplyKeyboardRemove())


@router.message(StateFilter(Onboarding.looking_for))
async def process_looking_for_invalid(message: Message) -> None:
    await message.answer("Выбери вариант на клавиатуре ниже", reply_markup=_gender_keyboard())


@router.message(StateFilter(Onboarding.city))
async def process_city(message: Message, state: FSMContext) -> None:
    await state.update_data(city=message.text.strip())
    await state.set_state(Onboarding.bio)
    await message.answer(
        "Расскажи немного о себе и своих интересах"
    )


@router.message(StateFilter(Onboarding.bio))
async def process_bio(message: Message, state: FSMContext) -> None:
    await state.update_data(bio_text=message.text.strip())
    await state.set_state(Onboarding.photo)
    await message.answer("Пришли свое фото")


@router.message(StateFilter(Onboarding.photo), F.photo)
async def process_photo(message: Message, state: FSMContext) -> None:
    data = await state.update_data(photo_file_id=message.photo[-1].file_id)
    await state.clear()

    embedding_service = get_embedding_service()
    embedding = embedding_service.encode(data["bio_text"])
    logger.debug("Построен эмбеддинг для пользователя %s", message.from_user.id)

    async with get_session() as session:
        await create_user(
            session,
            user_id=message.from_user.id,
            name=data["name"],
            age=data["age"],
            gender=data["gender"],
            looking_for=data["looking_for"],
            city=data["city"],
            bio_text=data["bio_text"],
            photo_file_id=data["photo_file_id"],
            embedding=embedding,
        )

    logger.info("Пользователь %s зарегистрирован", message.from_user.id)
    await message.answer(f"Анкета готова, {data['name']}!")


@router.message(StateFilter(Onboarding.photo))
async def process_photo_invalid(message: Message) -> None:
    await message.answer("Нужно именно фото, пришли его как изображение")
