from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from database.models import SentenceStatus


class SentencesRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db.suggested_sentences

    async def add(self, text: str, author: int) -> None:
        await self.col.insert_one({
            "text": text,
            "author": author,
            "status": SentenceStatus.PENDING,
            "moderator": None,
            "approved_at": None,
            "created_at": datetime.utcnow(),
        })

    async def random_approved(self, limit: int = 5) -> list[dict]:
        cursor = self.col.aggregate([
            {"$match": {"status": SentenceStatus.APPROVED}},
            {"$sample": {"size": limit}},
        ])
        return [doc async for doc in cursor]

    async def set_status(
        self, doc_id, status: SentenceStatus, moderator: int
    ) -> None:
        await self.col.update_one(
            {"_id": doc_id},
            {"$set": {
                "status": status,
                "moderator": moderator,
                "approved_at": datetime.utcnow(),
            }},
        )