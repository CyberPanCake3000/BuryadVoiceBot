from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from bson import ObjectId

from filters.reviewer import IsReviewer
from keyboards.review import review_kb
from database.mongo import Mongo
from database.repositories.sentences import SentencesRepository
from database.repositories.reviewers import ReviewersRepository
from database.repositories.users import UsersRepository

router = Router(name="startreview")
class ReviewState(StatesGroup):
    WAIT_EDIT = State()


EDIT_PROMPT = (
    "Введите исправленное предложение.\n\n"
    "Меняйте только ошибки (буква, запятая, точка). "
    "Смысл предложения не меняйте.\n\n"
    "Чтобы отменить — нажмите «Отменить» или напишите /cancel"
)


@router.message(Command("startreview"), IsReviewer())
async def cmd_startreview(message: Message, mongo: Mongo) -> None:
    await send_next_sentence(message, message.from_user.id, mongo)

COMPLAINTS_LIMIT = 3

@router.callback_query(F.data.startswith("rv:"))
async def on_review(callback: CallbackQuery, state: FSMContext, mongo: Mongo) -> None:
    # разбираем callback_data: "rv:approve:64f..." → decision="approve", sid="64f..."
    _, decision, sid = callback.data.split(":")

    sentences = SentencesRepository(mongo.db)
    reviewers = ReviewersRepository(mongo.db)
    users = UsersRepository(mongo.db)

    await callback.message.edit_reply_markup(reply_markup=None)

    if decision == "edit":
        await state.set_state(ReviewState.WAIT_EDIT)
        await state.update_data(sentence_id=sid)
        await callback.message.answer(EDIT_PROMPT)
        await callback.answer()
        return

    added = await sentences.add_review(ObjectId(sid), callback.from_user.id, decision)
    if added and decision == "complain":
        author_id = await sentences.get_author(ObjectId(sid))
        if author_id is not None:
            count = await users.add_complaint(author_id)
            if count >= COMPLAINTS_LIMIT:
                await users.ban(author_id)
                try:
                    await callback.bot.send_message(
                        author_id,
                        "Вы получили 3 жалобы и исключены из проекта. "
                        "Доступ к боту закрыт.",
                    )
                except Exception:
                    pass 
        await callback.answer("Жалоба отправлена")
    elif added and decision in ("approve", "reject"):
        await sentences.recalc_status(ObjectId(sid))
        await callback.answer("Учтено!")
    else:
        await callback.answer("Уже учтено")


async def send_next_sentence(message: Message, reviewer_id: int, mongo: Mongo) -> bool:
    repo = SentencesRepository(mongo.db)
    docs = await repo.random_unreviewed(reviewer_id, limit=1)
    if not docs:
        await message.answer("Новых предложений на модерацию нет 🎉")
        return False
    d = docs[0]
    await message.answer(d["text"], reply_markup=review_kb(str(d["_id"])))
    return True


@router.message(StateFilter(ReviewState.WAIT_EDIT), F.text)
async def on_edit_text(message: Message, state: FSMContext, mongo: Mongo) -> None:
    data = await state.get_data()
    sid = data["sentence_id"]
    new_text = message.text.strip()

    if not new_text or new_text.startswith("/"):
        await message.answer("Пришлите отредактированный текст предложения.")
        return

    sentences = SentencesRepository(mongo.db)
    ok = await sentences.add_edit_review(ObjectId(sid), message.from_user.id, new_text)

    await state.clear()

    if ok:
        await message.answer("Сохранено ✅")
    else:
        await message.answer("Не удалось сохранить (возможно, вы уже обрабатывали это предложение).")

    await send_next_sentence(message, message.from_user.id, mongo)