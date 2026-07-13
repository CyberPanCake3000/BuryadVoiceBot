from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from filters.admin import IsAdmin
from database.mongo import Mongo
from database.repositories.stats import StatsRepository

router = Router(name="reviewstat")


def _format_name(row: dict) -> str:
    return f"@{row['username']}" if row.get("username") else f"id{row['_id']}"


@router.message(Command("reviewstat"), IsAdmin())
async def cmd_reviewstat(message: Message, mongo: Mongo) -> None:
    repo = StatsRepository(mongo.db)
    sentence_rows = await repo.reviewer_stats()
    translation_rows = await repo.translation_reviewer_stats()

    if not sentence_rows and not translation_rows:
        await message.answer("Пока нет данных по ревьюерам.")
        return

    lines = ["📋 <b>Статистика ревьюеров</b>\n"]

    lines.append("<b>Модерация предложений</b>")
    if sentence_rows:
        for r in sentence_rows:
            lines.append(
                f"<b>{_format_name(r)}</b>\n"
                f"всего: {r.get('total', 0)}   "
                f"✅ {r.get('approved', 0)}   "
                f"❌ {r.get('rejected', 0)}   "
                f"✏️ {r.get('edited', 0)}   "
                f"🚫 {r.get('complained', 0)}"
            )
    else:
        lines.append("Пока нет данных.")

    lines.append("")
    lines.append("<b>Проверка переводов</b>")
    if translation_rows:
        for r in translation_rows:
            lines.append(
                f"<b>{_format_name(r)}</b>\n"
                f"всего: {r.get('total', 0)}   "
                f"✅ {r.get('approved', 0)}   "
                f"✏️ {r.get('edited', 0)}   "
                f"⏭ {r.get('skipped', 0)}"
            )
    else:
        lines.append("Пока нет данных.")

    await message.answer("\n".join(lines))