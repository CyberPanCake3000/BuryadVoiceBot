from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from database.mongo import Mongo
from database.repositories.sentences import SentencesRepository

router = Router(name="voice")


class VoiceState(StatesGroup):
    WAIT_VOICE = State()


@router.message(Command("voice"))
async def cmd_voice(message: Message, state: FSMContext, mongo: Mongo) -> None:
    repo = SentencesRepository(mongo.db)
    docs = await repo.random_approved(limit=5)
    if not docs:
        await message.answer("Пока нет одобренных предложений для озвучки.")
        return

    await state.set_state(VoiceState.WAIT_VOICE)
    await state.update_data(queue=[str(d["_id"]) for d in docs], index=0)
    await message.answer(
        f"Предложение №1:\n\n<b>{docs[0]['text']}</b>\n\nПришлите голосовое сообщение."
    )


@router.message(StateFilter(VoiceState.WAIT_VOICE), F.voice)
async def on_voice(message: Message, state: FSMContext, mongo: Mongo) -> None:
    ...