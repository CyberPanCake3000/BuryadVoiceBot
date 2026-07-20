from html import escape

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from bson import ObjectId

from database.mongo import Mongo
from database.repositories.translations import NeedTranslationRepository
from filters.reviewer import IsReviewer
from keyboards.checktranslation import check_translation_kb

router = Router(name="checktranslation")


BRIEFING = (
    "📋 <b>Памятка по проверке переводов</b>\n\n"
    "• Не меняйте смысл предложения\n"
    "• Не изменяйте HTML-теги и спецсимволы ({ $var } и т.п.)\n"
    "• Исправляйте только грамматические и логические ошибки\n"
    "• Этот перевод выполнен LLM — точность может быть низкой, "
    "ваша задача — поправить ошибки\n\n"
    "Начинаем 👇"
)

EDIT_PROMPT = (
    "Введите исправленный перевод.\n\n"
    "Смысл, теги и служебные знаки не меняйте.\n"
    "Отмена — «Отменить» или /cancel"
)


class CheckTranslationState(StatesGroup):
    ACTIVE = State()
    WAIT_EDIT = State()


def _format_item(item: dict) -> str:
    markup_warn = (
        "⚠️ <i>Строка содержит разметку — проверьте теги и переменные</i>\n\n"
        if item.get("has_markup")
        else ""
    )
    return (
        f"{markup_warn}"
        f"<b>Оригинал:</b>\n{escape(item['source_text'])}\n\n"
        f"<b>Перевод:</b>\n{escape(item['translation'])}"
    )


def _doc_to_queue_item(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "source_text": doc["source_text"],
        "translation": doc["translation"],
        "mt_draft": doc["mt_draft"],
        "has_markup": doc.get("has_markup", False),
    }


async def _ensure_briefing(message: Message, mongo: Mongo, reviewer_id: int) -> None:
    doc = await mongo.db.reviewers.find_one(
        {"telegram_id": reviewer_id},
        {"translation_briefing_seen": 1},
    )
    if doc and doc.get("translation_briefing_seen"):
        return
    await message.answer(BRIEFING)
    await mongo.db.reviewers.update_one(
        {"telegram_id": reviewer_id},
        {"$set": {"translation_briefing_seen": True}},
    )


async def send_next_item(message: Message, state: FSMContext, mongo: Mongo) -> None:
    data = await state.get_data()
    queue = data.get("queue", [])
    if not queue:
        await state.clear()
        await message.answer("Готово! Спасибо за проверку переводов 🙏")
        return

    current = queue[0]
    await message.answer(
        _format_item(current),
        reply_markup=check_translation_kb(current["id"]),
    )


async def resend_current_item(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    queue = data.get("queue", [])
    if not queue:
        return
    current = queue[0]
    await message.answer(
        _format_item(current),
        reply_markup=check_translation_kb(current["id"]),
    )


@router.message(Command("checktranslation"), IsReviewer())
async def cmd_checktranslation(message: Message, state: FSMContext, mongo: Mongo) -> None:
    await _ensure_briefing(message, mongo, message.from_user.id)

    repo = NeedTranslationRepository(mongo.db)
    docs = await repo.random_unseen(message.from_user.id, limit=3)
    if not docs:
        await message.answer("Предложений для проверки пока нет 🎉")
        return

    queue = [_doc_to_queue_item(d) for d in docs]
    await state.set_state(CheckTranslationState.ACTIVE)
    await state.update_data(queue=queue, edit_id=None, edit_mt_draft=None)
    await send_next_item(message, state, mongo)


@router.callback_query(F.data.startswith("ct:"))
async def on_check_translation(callback: CallbackQuery, state: FSMContext, mongo: Mongo) -> None:
    if await state.get_state() != CheckTranslationState.ACTIVE:
        await callback.answer("Сначала вызовите /checktranslation")
        return

    _, decision, doc_id = callback.data.split(":")
    data = await state.get_data()
    queue = data.get("queue", [])
    if not queue or queue[0]["id"] != doc_id:
        await callback.answer("Эта строка уже не актуальна")
        return

    await callback.message.edit_reply_markup(reply_markup=None)
    repo = NeedTranslationRepository(mongo.db)
    oid = ObjectId(doc_id)
    reviewer_id = callback.from_user.id

    if decision == "edit":
        await state.set_state(CheckTranslationState.WAIT_EDIT)
        await state.update_data(
            edit_id=doc_id,
            edit_mt_draft=queue[0]["mt_draft"],
        )
        await callback.message.answer(EDIT_PROMPT)
        await callback.answer()
        return

    if decision == "approve":
        ok = await repo.approve(oid, reviewer_id)
        feedback = "Принято ✅" if ok else "Эта строка уже обработана, пропускаем."
    else:
        ok = await repo.skip(oid, reviewer_id)
        feedback = "Пропущено ⏭" if ok else "Эта строка уже обработана, пропускаем."

    await callback.message.answer(feedback)
    queue.pop(0)
    await state.update_data(queue=queue)
    await send_next_item(callback.message, state, mongo)
    await callback.answer()


@router.message(StateFilter(CheckTranslationState.WAIT_EDIT), F.text)
async def on_edit_text(message: Message, state: FSMContext, mongo: Mongo) -> None:
    data = await state.get_data()
    doc_id = data.get("edit_id")
    mt_draft = data.get("edit_mt_draft", "")
    new_text = message.text.strip()

    if not new_text or new_text.startswith("/"):
        await message.answer("Пришлите исправленный перевод.")
        return

    repo = NeedTranslationRepository(mongo.db)
    ok = await repo.approve_edited(ObjectId(doc_id), message.from_user.id, new_text, mt_draft)

    queue = data.get("queue", [])
    if ok and queue and queue[0]["id"] == doc_id:
        queue.pop(0)

    await state.set_state(CheckTranslationState.ACTIVE)
    await state.update_data(queue=queue, edit_id=None, edit_mt_draft=None)

    if ok:
        await message.answer("Сохранено ✅")
    else:
        await message.answer("Не удалось сохранить (возможно, вы уже обрабатывали эту строку).")

    await send_next_item(message, state, mongo)