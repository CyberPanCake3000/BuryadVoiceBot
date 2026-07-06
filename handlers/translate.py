from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from database.mongo import Mongo
from database.repositories.translations import TranslationsRepository

router = Router(name="translate")


class TranslateState(StatesGroup):
    WAIT_TRANSLATION = State()


@router.message(Command("translate"))
async def cmd_translate(message: Message, state: FSMContext, mongo: Mongo) -> None:
    repo = TranslationsRepository(mongo.db)
    docs = await repo.random(limit=5)
    if not docs:
        await message.answer("Пока нет предложений для перевода.")
        return

    await state.set_state(TranslateState.WAIT_TRANSLATION)
    await state.update_data(queue=[str(d["_id"]) for d in docs], index=0)
    await message.answer(f"Переведите:\n\n<b>{docs[0]['text']}</b>")


@router.message(StateFilter(TranslateState.WAIT_TRANSLATION))
async def on_translation(message: Message, state: FSMContext, mongo: Mongo) -> None:
    # TODO: сохранить перевод, показать следующее предложение или "Спасибо!"
    ...