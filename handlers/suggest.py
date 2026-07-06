from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from database.mongo import Mongo
from database.repositories.sentences import SentencesRepository

router = Router(name="suggest")


class SuggestState(StatesGroup):
    WAIT_SENTENCE = State()


@router.message(Command("suggest"))
async def cmd_suggest(message: Message, state: FSMContext) -> None:
    await state.set_state(SuggestState.WAIT_SENTENCE)
    await message.answer(
        "Введите предложение на бурятском.\n"
        "Оно попадёт на модерацию.\n"
        "После одобрения его смогут озвучить другие пользователи."
    )


@router.message(StateFilter(SuggestState.WAIT_SENTENCE))
async def on_sentence(message: Message, state: FSMContext, mongo: Mongo) -> None:
    repo = SentencesRepository(mongo.db)
    await repo.add(text=message.text, author=message.from_user.id)
    await state.clear()
    await message.answer("Спасибо! Предложение отправлено на модерацию.")