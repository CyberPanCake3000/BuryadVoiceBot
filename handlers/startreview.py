from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from bson import ObjectId

from filters.reviewer import IsReviewer
from keyboards.review import review_kb
from database.mongo import Mongo
from database.repositories.sentences import SentencesRepository
from database.repositories.reviewers import ReviewersRepository
from database.repositories.users import UsersRepository

router = Router(name="startreview")

@router.message(Command("startreview"), IsReviewer())
async def cmd_startreview(message: Message, mongo: Mongo) -> None:
    repo = SentencesRepository(mongo.db)
    docs = await repo.random_unreviewed(message.from_user.id, limit=5)
    if not docs:
        await message.answer("Новых предложений на модерацию нет 🎉")
        return
    for d in docs:
        await message.answer(d["text"], reply_markup=review_kb(str(d["_id"])))

COMPLAINTS_LIMIT = 3

@router.callback_query(F.data.startswith("rv:"))
async def on_review(callback: CallbackQuery, mongo: Mongo) -> None:
    # разбираем callback_data: "rv:approve:64f..." → decision="approve", sid="64f..."
    _, decision, sid = callback.data.split(":")

    sentences = SentencesRepository(mongo.db)
    reviewers = ReviewersRepository(mongo.db)
    users = UsersRepository(mongo.db)

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
        total = await reviewers.count()
        await sentences.recalc_status(ObjectId(sid), total)
        await callback.answer("Учтено!")
    else:
        await callback.answer("Уже учтено")
    await callback.message.edit_reply_markup(reply_markup=None)