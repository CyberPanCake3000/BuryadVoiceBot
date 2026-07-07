from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase


class ReviewersRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db.reviewers

    async def add(self, telegram_id, username, full_name, added_by) -> None:
        await self.col.update_one(
            {"telegram_id": telegram_id},
            {"$setOnInsert": {
                "telegram_id": telegram_id,
                "username": username,
                "full_name": full_name,
                "added_by": added_by,
                "created_at": datetime.utcnow(),
            }},
            upsert=True,
        )

    async def is_reviewer(self, telegram_id: int) -> bool:
        return await self.col.find_one({"telegram_id": telegram_id}, {"_id": 1}) is not None

    async def count(self) -> int:
        return await self.col.count_documents({})

    async def set_username(self, telegram_id: int, username: str | None) -> None:
        await self.col.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"username": username}},
        )