from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from bson import ObjectId

from database.mongo import Mongo
from database.repositories.translations import NeedTranslationRepository
from filters.admin import IsAdmin
from keyboards.filltranslation import fill_translation_kb

router = Router(name="filltranslation")


class FillTranslationState(StatesGroup):
    ACTIVE = State()


def _format_item(item: dict) -> str:
    return (
        f"<b>Оригинал:</b>\n{escape(item['source_text'])}\n\n"
        f"<b>Перевод:</b>\n{escape(item['translation'])}\n\n"
        f"🔗 {escape(item['source_url'])}"
    )


async def send_next_item(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    queue = data.get("queue", [])
    if not queue:
        await state.clear()
        await message.answer("Готово! Все 3 перевода отмечены как заполненные")
        return

    current = queue[0]
    await message.answer(
        _format_item(current),
        reply_markup=fill_translation_kb(current["id"]),
        disable_web_page_preview=True,
    )


@router.message(Command("filltranslation"), IsAdmin())
async def cmd_filltranslation(message: Message, state: FSMContext, mongo: Mongo) -> None:
    current = await state.get_state()
    if current == FillTranslationState.ACTIVE.state:
        await message.answer(
            "У вас уже идёт заполнение.\n"
            "Продолжите с кнопок или завершите — /cancel"
        )
        return

    repo = NeedTranslationRepository(mongo.db)
    docs = await repo.random_approved(limit=3)
    if not docs:
        await message.answer("Нет одобренных переводов для заполнения в Pontoon 🎉")
        return

    queue = [{
        "id": str(d["_id"]),
        "source_text": d["source_text"],
        "translation": d.get("translation") or d.get("mt_draft", ""),
        "source_url": d.get("source_url", ""),
    } for d in docs]

    await state.set_state(FillTranslationState.ACTIVE)
    await state.update_data(queue=queue)
    await send_next_item(message, state)


@router.callback_query(F.data.startswith("ft:"), IsAdmin())
async def on_fill_done(callback: CallbackQuery, state: FSMContext, mongo: Mongo) -> None:
    if await state.get_state() != FillTranslationState.ACTIVE:
        await callback.answer("Сначала вызовите /filltranslation", show_alert=True)
        return

    _, decision, doc_id = callback.data.split(":")
    if decision != "done":
        await callback.answer()
        return

    data = await state.get_data()
    queue = data.get("queue", [])
    if not queue or queue[0]["id"] != doc_id:
        await callback.answer("Это сообщение устарело", show_alert=True)
        return

    await callback.message.edit_reply_markup(reply_markup=None)

    repo = NeedTranslationRepository(mongo.db)
    ok = await repo.mark_recorded(ObjectId(doc_id), callback.from_user.id)

    await callback.message.answer(
        "Отмечено как заполненное ✅" if ok else "Уже было отмечено, пропускаем."
    )

    queue.pop(0)
    await state.update_data(queue=queue)
    await send_next_item(callback.message, state)
    await callback.answer()