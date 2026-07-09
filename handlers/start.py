from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from database.mongo import Mongo
from database.repositories.users import UsersRepository
from keyboards.agreement import agreement_kb
from keyboards.menu import main_menu_kb
from services.roles import get_role
from database.repositories.reviewers import ReviewersRepository

router = Router(name="start")

WELCOME = (
    "Сайнуу!\n\n"
    "Этот бот помогает собрать корпус бурятского языка "
    "для проекта Mozilla Common Voice.\n\n"
    "Что умеет бот:\n"
    "/suggest — предложить новое предложение\n"
    "/voice — озвучить предложения\n"
    "/leaderboard — посмотреть топ-5 участников\n"
    "/stat — посмотреть статистику\n"
    "/cancel — отменить текущее действие\n\n"
    "Перед использованием необходимо согласиться "
    "с политикой обработки данных. Прочитать подробнее политику можно используя команду /policy"
)

ADMIN_WELCOME = (
    "Вы вошли как <b>администратор</b>.\n\n"
    "Доступные действия:\n"
    "/addreviewer — добавить ревьюера (отправьте контакт)\n"
    "/suggest — предложить предложение\n"
    "/voice — озвучить предложения\n"
    "/leaderboard — посмотреть топ-5 участников\n"
    "/stat — посмотреть статистику\n"
    "/cancel — отменить текущее действие\n"
    "/addfortranslation — добавить текста из UI сайта для перевода"
)

REVIEWER_WELCOME = (
    "Вы — <b>ревьюер</b>.\n\n"
    "Вы помогаете модерировать предложения других участников.\n"
    "/startreview — получить предложения на проверку\n"
    "/suggest — предложить своё\n"
    "/voice — озвучить предложения\n"
    "/leaderboard — посмотреть топ-5 участников\n"
    "/translate — перевести текста из UI сайта\n"
    "/stat — посмотреть статистику\n"
    "/cancel — отменить текущее действие\n\n"
)

@router.message(CommandStart())
async def cmd_start(message: Message, mongo: Mongo) -> None:
    users = UsersRepository(mongo.db)
    await users.upsert(message.from_user.id, message.from_user.username)
    role = await get_role(message.from_user.id, mongo)
    if role == "reviewer":
        reviewers = ReviewersRepository(mongo.db)
        await reviewers.set_username(message.from_user.id, message.from_user.username)
    
    if not await users.is_agreed(message.from_user.id):
        await message.answer(WELCOME, reply_markup=agreement_kb())
        return
    
    if role == "admin":
        await message.answer(ADMIN_WELCOME, reply_markup=main_menu_kb("admin"))
        return
    if role == "reviewer":
        await message.answer(REVIEWER_WELCOME, reply_markup=main_menu_kb("reviewer"))
        return
    if await users.is_agreed(message.from_user.id):
        await message.answer("С возвращением!", reply_markup=main_menu_kb("user"))
    else:
        await message.answer(WELCOME, reply_markup=agreement_kb())


@router.callback_query(F.data == "agree")
async def on_agree(callback: CallbackQuery, mongo: Mongo) -> None:
    users = UsersRepository(mongo.db)
    await users.set_agreed(callback.from_user.id)

    role = await get_role(callback.from_user.id, mongo)
    welcome = {
        "admin": ADMIN_WELCOME,
        "reviewer": REVIEWER_WELCOME,
    }.get(role, "Спасибо! Теперь Вам доступны все команды.")

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(welcome, reply_markup=main_menu_kb(role))
    await callback.answer()