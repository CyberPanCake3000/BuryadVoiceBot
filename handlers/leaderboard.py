from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.mongo import Mongo
from database.repositories.stats import StatsRepository

router = Router(name="leaderboard")

MEDALS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]


@router.message(Command("leaderboard"))
async def cmd_leaderboard(message: Message, mongo: Mongo) -> None:
    repo = StatsRepository(mongo.db)
    rows = await repo.top(limit=5)
    if not rows:
        await message.answer("Пока нет данных для рейтинга 🤷")
        return

    lines = ["🏆 <b>Топ-5 участников</b>\n"]
    for i, r in enumerate(rows):
        name = f"@{r['username']}" if r.get("username") else f"id{r['_id']}"
        lines.append(
            f"{MEDALS[i]} <b>{name}</b>\n"
            f"войсы: {r.get('voices', 0)}\n"
            f"предложения: {r.get('suggestions', 0)}\n"
            f"ревью: {r.get('reviews', 0)}\n"
            f"проверенные переводы: {r.get('translation_reviews', 0)}\n"
            f"рейтинг: {r.get('rating', 0)}\n\n"
        )
    await message.answer("\n".join(lines))