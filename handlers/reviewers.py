from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from filters.admin import IsAdmin
from database.mongo import Mongo
from database.repositories.reviewers import ReviewersRepository
from database.repositories.users import UsersRepository

router = Router(name="reviewers")


class AddReviewerState(StatesGroup):
    WAIT_CONTACT = State()


@router.message(Command("addreviewer"), IsAdmin())
async def cmd_addreviewer(message: Message, state: FSMContext) -> None:
    await state.set_state(AddReviewerState.WAIT_CONTACT)
    await message.answer("Отправьте контакт пользователя, которого хотите сделать ревьюером.")

@router.message(AddReviewerState.WAIT_CONTACT, F.text)
async def on_identifier(message: Message, state: FSMContext, mongo: Mongo) -> None:
    users = UsersRepository(mongo.db)
    text = message.text.strip()
    uname = text.lstrip("@")
    user = await users.get_by_username(uname)
    if not user:
        await message.answer("Пользователь не найден. Он должен сначала запустить бота.")
        return
    target_id, username = user["telegram_id"], uname
    full_name = None

    repo = ReviewersRepository(mongo.db)
    await repo.add(target_id, username, full_name, message.from_user.id)
    await state.clear()
    await message.answer("Готово! Пользователь теперь ревьюер.")

@router.message(AddReviewerState.WAIT_CONTACT, F.contact)
async def on_contact(message: Message, state: FSMContext, mongo: Mongo) -> None:
    contact = message.contact
    if contact.user_id is None:
        await message.answer("У этого контакта нет Telegram-аккаунта. Нужен пользователь Telegram.")
        return
    repo = ReviewersRepository(mongo.db)
    full_name = " ".join(filter(None, [contact.first_name, contact.last_name]))
    await repo.add(contact.user_id, None, full_name, message.from_user.id)
    await state.clear()
    await message.answer(f"Готово! {full_name} теперь ревьюер.")