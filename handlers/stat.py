from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import F

from database.mongo import Mongo
from database.repositories.stats import StatsRepository

router = Router(name="stats")


@router.message(Command("stat"))
@router.message(F.text == "Наши итоги")
async def cmd_stat(message: Message, mongo: Mongo) -> None:
    repo = StatsRepository(mongo.db)
    s = await repo.overview()

    text = (
        "<b>Статистика проекта</b>\n\n"
        f"👥 Участников: <b>{s['participants']}</b>\n"
        f"✍️ Предложений добавлено: <b>{s['total_suggestions']}</b>\n"
        f"✅ Из них принято: <b>{s['approved']}</b>\n"
        f"🌐 Переводов проверено: <b>{s['translated']}</b>\n"
        f"📥 Заполнено внесено на сайт: <b>{s['recorded']}</b>\n"
        f"🎙 Голосовых записей: <b>{s['total_voices']}</b>\n\n"
        "Баярлалаа! Спасибо за помощь в сохранении бурятского языка! 🙏"
    )
    await message.answer(text)