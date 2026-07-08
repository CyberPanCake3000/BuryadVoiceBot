from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from bson import ObjectId

from filters.reviewer import IsReviewer
from database.mongo import Mongo
from database.repositories.translations import NeedTranslationRepository

router = Router(name="translate")


class TranslateState(StatesGroup):
    WAIT_TRANSLATION = State()


async def _send_next(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    queue = data.get("queue", [])
    if not queue:
        await state.clear()
        await message.answer("Готово! Спасибо за переводы 🙏")
        return
    current = queue[0]
    await state.update_data(queue=queue)
    await message.answer(f"Переведите:\n\n<b>{current['text']}</b>")


@router.message(Command("translate"), IsReviewer())
async def cmd_translate(message: Message, state: FSMContext, mongo: Mongo) -> None:
    repo = NeedTranslationRepository(mongo.db)
    docs = await repo.random_pending(limit=3)
    if not docs:
        await message.answer("Предложений для перевода пока нет 🎉")
        return
    queue = [{"id": str(d["_id"]), "text": d["text"]} for d in docs]
    await state.set_state(TranslateState.WAIT_TRANSLATION)
    await state.update_data(queue=queue)
    await _send_next(message, state)


@router.message(TranslateState.WAIT_TRANSLATION, F.text)
async def on_translation(message: Message, state: FSMContext, mongo: Mongo) -> None:
    data = await state.get_data()
    queue = data.get("queue", [])
    if not queue:
        await state.clear()
        return
    current = queue.pop(0)

    repo = NeedTranslationRepository(mongo.db)
    ok = await repo.set_translation(
        ObjectId(current["id"]), message.from_user.id, message.text.strip()
    )
    await message.answer("Сохранено ✅" if ok else "Это предложение уже перевели, пропускаем.")

    await state.update_data(queue=queue)
    await _send_next(message, state)