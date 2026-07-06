from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from database.mongo import Mongo
from database.repositories.users import UsersRepository
from keyboards.agreement import agreement_kb
from keyboards.menu import main_menu_kb

router = Router(name="start")

WELCOME = (
    "Сайнуу!\n\n"
    "Этот бот помогает собрать корпус бурятского языка "
    "для проекта Mozilla Common Voice.\n\n"
    "Что умеет бот:\n"
    "/translate — помочь с переводом предложений\n"
    "/suggest — предложить новое предложение\n"
    "/voice — озвучить предложения\n\n"
    "Перед использованием необходимо согласиться "
    "с политикой обработки данных."
)


@router.message(CommandStart())
async def cmd_start(message: Message, mongo: Mongo) -> None:
    users = UsersRepository(mongo.db)
    await users.upsert(message.from_user.id, message.from_user.username)
    await message.answer(WELCOME, reply_markup=agreement_kb())


@router.callback_query(F.data == "agree")
async def on_agree(callback: CallbackQuery, mongo: Mongo) -> None:
    users = UsersRepository(mongo.db)
    await users.set_agreed(callback.from_user.id)
    await callback.message.answer(
        "Спасибо! Теперь доступны все команды.",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()