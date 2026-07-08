from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.mongo import Mongo
from database.repositories.stats import StatsRepository

router = Router(name="stats")


@router.message(Command("stat"))
async def cmd_stat(message: Message, mongo: Mongo) -> None:
    repo = StatsRepository(mongo.db)
    s = await repo.overview()

    text = (
        "<b>Статистика проекта</b>\n\n"
        f"👥 Участников: <b>{s['participants']}</b>\n"
        f"✍️ Предложений добавлено: <b>{s['total_suggestions']}</b>\n"
        f"✅ Из них одобрено: <b>{s['approved']}</b>\n"
        f"🌐 Текстов переведено: <b>{s['translated']}</b>\n"
        f"🎙 Голосовых записей: <b>{s['total_voices']}</b>\n\n"
        "Спасибо, что помогаете сохранить бурятский язык! 🙏"
    )
    await message.answer(text)