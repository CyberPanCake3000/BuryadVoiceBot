from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from filters.admin import IsAdmin
from database.mongo import Mongo
from database.repositories.stats import StatsRepository

router = Router(name="reviewstat")


@router.message(Command("reviewstat"), IsAdmin())
async def cmd_reviewstat(message: Message, mongo: Mongo) -> None:
    repo = StatsRepository(mongo.db)
    rows = await repo.reviewer_stats()

    if not rows:
        await message.answer("Пока нет данных по ревьюерам.")
        return

    lines = ["📋 <b>Статистика ревьюеров</b>\n"]
    for r in rows:
        name = f"@{r['username']}" if r.get("username") else f"id{r['_id']}"
        lines.append(
            f"<b>{name}</b>\n"
            f"всего: {r.get('total', 0)}   "
            f"✅ {r.get('approved', 0)}   "
            f"❌ {r.get('rejected', 0)}   "
            f"✏️ {r.get('edited', 0)}   "
            f"🚫 {r.get('complained', 0)}"
        )

    await message.answer("\n".join(lines))