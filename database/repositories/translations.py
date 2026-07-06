from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase


class TranslationsRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db.need_translation

    async def random(self, limit: int = 5, locale: str = "en") -> list[dict]:
        cursor = self.col.aggregate([
            {"$match": {"locale": locale}},
            {"$sample": {"size": limit}},
        ])
        return [doc async for doc in cursor]

    async def add_translation(
        self, doc_id, telegram_id: int, text: str
    ) -> None:
        await self.col.update_one(
            {"_id": doc_id},
            {"$push": {"translations": {
                "telegram_id": telegram_id,
                "text": text,
                "created_at": datetime.utcnow(),
            }}},
        )