from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from database.mongo import Mongo
from database.repositories.sentences import SentencesRepository
from database.repositories.users import UsersRepository
from bson import ObjectId
from database.repositories.voices import VoicesRepository

router = Router(name="voice")

VOICE_HINT = (
    "Здравствуйте! Вот правила записи голоса:\n\n"
    "• Записывайте в тихом месте, без посторонних шумов.\n"
    "• Говорите чётко и прочитайте предложение целиком.\n"
    "• Одно голосовое сообщение — одно предложение.\n\n"
    "<i>Эта памятка показывается только один раз.</i>"
)

class VoiceState(StatesGroup):
    WAIT_VOICE = State()


@router.message(Command("voice"))
@router.message(F.text == "Озвучить")
async def cmd_voice(message: Message, state: FSMContext, mongo: Mongo) -> None:
    repo = SentencesRepository(mongo.db)
    docs = await repo.random_approved(limit=5)
    if not docs:
        await message.answer("Пока нет готовых фраз для озвучки. Загляните позже.")
        return

    users = UsersRepository(mongo.db)
    if await users.mark_hint_seen(message.from_user.id, "voice"):
        await message.answer(VOICE_HINT)

    await state.set_state(VoiceState.WAIT_VOICE)
    await state.update_data(
        queue=[{"id": str(d["_id"]), "text": d["text"]} for d in docs],
        index=0,
    )
    await message.answer(
        f"Прочитайте вслух:\n\n<b>{docs[0]['text']}</b>\n\nПришлите голосовое сообщение."
    )


@router.message(StateFilter(VoiceState.WAIT_VOICE), F.voice)
async def on_voice(message: Message, state: FSMContext, mongo: Mongo) -> None:
    data = await state.get_data()
    queue = data["queue"]
    index = data["index"]
    current = queue[index]

    voice = message.voice
    voices = VoicesRepository(mongo.db)
    await voices.add(
        sentence_id=ObjectId(current["id"]),
        telegram_id=message.from_user.id,
        file_id=voice.file_id,
        unique_id=voice.file_unique_id,
        duration=voice.duration,
    )

    await message.answer("Спасибо! Каждый голос важен 🙏")

    index += 1
    if index < len(queue):
        await state.update_data(index=index)
        nxt = queue[index]
        await message.answer(
            f"Предложение №{index + 1}:\n\n<b>{nxt['text']}</b>\n\nПришлите голосовое сообщение."
        )
    else:
        await state.clear()
        await message.answer("Готово! Вы озвучили все предложения. Баярлалаа!")


@router.message(StateFilter(VoiceState.WAIT_VOICE))
async def not_a_voice(message: Message) -> None:
    await message.answer("Пожалуйста, пришлите именно голосовое сообщение 🎤")