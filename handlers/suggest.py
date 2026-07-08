from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from bson import ObjectId

from database.mongo import Mongo
from database.repositories.sentences import SentencesRepository
from database.repositories.voices import VoicesRepository
from database.repositories.users import UsersRepository
from keyboards.suggest import suggest_voice_kb

router = Router(name="suggest")

SUGGEST_HINT = (
    "Здравствуйте! Вот правила по текстовым данным:\n\n"
    "• Присылайте предложение на бурятском языке, например:\n"
    "<i>Сайн байна!</i>\n"
    "• Без личных данных, ссылок и оскорблений.\n\n"
    "• Введенные предложения проходят модерацию, после чего их смогут озвучить другие участники.\n\n"
    "• Ревьюер может пожаловаться на предложение, после получения 3 жалоб одним пользователем этот пользователь будет исключен из программы.\n\n"
    "<i>Эта памятка показывается только один раз.</i>"
)

class SuggestState(StatesGroup):
    WAIT_SENTENCE = State()
    WAIT_DECISION = State()
    WAIT_VOICE = State()

@router.message(Command("suggest"))
async def cmd_suggest(message: Message, state: FSMContext, mongo: Mongo) -> None:
    users = UsersRepository(mongo.db)
    if await users.mark_hint_seen(message.from_user.id, "suggest"):
        await message.answer(SUGGEST_HINT)

    await state.set_state(SuggestState.WAIT_SENTENCE)
    await message.answer(
        "Предложите <b>своё</b> предложение на бурятском языке.\n\n"
        "Например: <i>Сайн байна!</i>\n\n"
        "Оно попадёт на модерацию, а после одобрения его смогут озвучить другие участники.",
    )


@router.message(StateFilter(SuggestState.WAIT_SENTENCE))
async def on_sentence(message: Message, state: FSMContext, mongo: Mongo) -> None:
    repo = SentencesRepository(mongo.db)
    sentence_id = await repo.add(text=message.text, author=message.from_user.id)

    await state.update_data(sentence_id=str(sentence_id), text=message.text)
    await state.set_state(SuggestState.WAIT_DECISION)

    await message.answer(
        "Спасибо! Предложение отправлено на модерацию.\n\n"
        "Желаете озвучить своё предложение?",
        reply_markup=suggest_voice_kb(),
    )


@router.callback_query(F.data == "sv:no")
async def on_decline(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Хорошо! Спасибо за ваш вклад 🙏")
    await callback.answer()


@router.callback_query(F.data == "sv:yes")
async def on_accept(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(SuggestState.WAIT_VOICE)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"Вот предложение:\n\n<b>{data['text']}</b>\n\n"
        "Озвучьте, пожалуйста — пришлите голосовое сообщение."
    )
    await callback.answer()


@router.message(StateFilter(SuggestState.WAIT_VOICE), F.voice)
async def on_suggest_voice(message: Message, state: FSMContext, mongo: Mongo) -> None:
    data = await state.get_data()
    voice = message.voice
    voices = VoicesRepository(mongo.db)
    await voices.add(
        sentence_id=ObjectId(data["sentence_id"]),
        telegram_id=message.from_user.id,
        file_id=voice.file_id,
        unique_id=voice.file_unique_id,
        duration=voice.duration,
    )
    await state.clear()
    await message.answer("Спасибо! Каждый голос важен 🙏")


@router.message(StateFilter(SuggestState.WAIT_VOICE))
async def suggest_not_voice(message: Message) -> None:
    await message.answer("Пожалуйста, пришлите именно голосовое сообщение 🎤")