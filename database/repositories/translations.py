from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase


class NeedTranslationRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db.need_translation

    async def add_many(self, texts: list[str], added_by: int) -> int:
        docs = [{
            "text": t,
            "translation": None,
            "translated_by": None,
            "status": "pending",
            "added_by": added_by,
            "translated_at": None,
            "created_at": datetime.utcnow(),
        } for t in texts if t.strip()]
        if not docs:
            return 0
        result = await self.col.insert_many(docs)
        return len(result.inserted_ids)

    async def random_pending(self, limit: int = 3) -> list[dict]:
        cursor = self.col.aggregate([
            {"$match": {"status": "pending"}},
            {"$sample": {"size": limit}},
        ])
        return [doc async for doc in cursor]

    async def set_translation(self, doc_id, reviewer_id: int, translation: str) -> bool:
        result = await self.col.update_one(
            {"_id": doc_id, "status": "pending"},
            {"$set": {
                "translation": translation,
                "translated_by": reviewer_id,
                "status": "translated",
                "translated_at": datetime.utcnow(),
            }},
        )
        return result.modified_count == 1