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
    "Этот помощник собирает фразы и голоса бурятского языка "
    "для открытого проекта Common Voice.\n\n"
    "Что можно сделать:\n"
    "• Предложить фразу — прислать предложение на бурятском\n"
    "• Озвучить — прочитать фразу вслух\n"
    "• Лучшие участники — посмотреть, кто больше всех помог\n"
    "• Наши итоги — сколько уже собрано\n"
    "• Отменить — остановить текущий шаг\n\n"
    "Перед началом нужно согласиться с правилами использования данных.\n"
    "Подробнее: напишите /policy"
)

ADMIN_WELCOME = (
    "Сайнуу! Вы вошли как <b>управляющий</b>.\n\n"
    "Доступно:\n"
    "• Добавить проверяющего — отправьте контакт человека\n"
    "• Предложить фразу / Озвучить\n"
    "• Лучшие участники / Наши итоги\n"
    "• Внести перевод — перенести готовые переводы на сайт\n"
    "• Отчёт проверяющих — сколько кто проверил\n"
    "• Отменить — остановить текущий шаг"
)

REVIEWER_WELCOME = (
    "Сайнуу! Вы — <b>проверяющий</b>.\n\n"
    "Вы помогаете отбирать хорошие фразы и переводы.\n\n"
    "Доступно:\n"
    "• Проверить фразы — разобрать предложения участников\n"
    "• Проверить перевод — поправить компьютерный перевод\n"
    "• Предложить фразу / Озвучить\n"
    "• Лучшие участники / Наши итоги\n"
    "• Отменить — остановить текущий шаг"
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
        await message.answer("Сайнуу снова! Рады вас видеть.", reply_markup=main_menu_kb("user"))
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
    }.get(role, "Баярлалаа! Теперь можно пользоваться всеми кнопками.")

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(welcome, reply_markup=main_menu_kb(role))
    await callback.answer()