from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from filters.admin import IsAdmin
from database.mongo import Mongo
from database.repositories.translations import NeedTranslationRepository

router = Router(name="addfortranslation")


class AddForTranslationState(StatesGroup):
    WAIT_TEXT = State()


@router.message(Command("addfortranslation"), IsAdmin())
async def cmd_add(message: Message, state: FSMContext) -> None:
    await state.set_state(AddForTranslationState.WAIT_TEXT)
    await message.answer(
        "Пришлите предложения для перевода.\n"
        "Можно несколько — каждое с новой строки."
    )


@router.message(AddForTranslationState.WAIT_TEXT, F.text)
async def on_text(message: Message, state: FSMContext, mongo: Mongo) -> None:
    repo = NeedTranslationRepository(mongo.db)
    texts = [line.strip() for line in message.text.splitlines() if line.strip()]
    added = await repo.add_many(texts, message.from_user.id)
    await state.clear()
    await message.answer(f"Добавлено предложений: {added}")