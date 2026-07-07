from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from filters.admin import IsAdmin
from database.mongo import Mongo
from database.repositories.reviewers import ReviewersRepository

router = Router(name="reviewers")


class AddReviewerState(StatesGroup):
    WAIT_CONTACT = State()


@router.message(Command("addreviewer"), IsAdmin())
async def cmd_addreviewer(message: Message, state: FSMContext) -> None:
    await state.set_state(AddReviewerState.WAIT_CONTACT)
    await message.answer("Отправьте контакт пользователя, которого хотите сделать ревьюером.")


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