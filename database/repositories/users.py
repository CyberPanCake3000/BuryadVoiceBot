from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument


class UsersRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db.users

    async def get(self, telegram_id: int) -> dict | None:
        return await self.col.find_one({"telegram_id": telegram_id})

    async def upsert(self, telegram_id: int, username: str | None) -> None:
        await self.col.update_one(
            {"telegram_id": telegram_id},
            {
                "$setOnInsert": {
                    "telegram_id": telegram_id,
                    "agreed": False,
                    "created_at": datetime.utcnow(),
                },
                "$set": {"username": username},
            },
            upsert=True,
        )

    async def set_agreed(self, telegram_id: int) -> None:
        await self.col.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"agreed": True, "agreed_at": datetime.utcnow()}},
        )

    async def is_agreed(self, telegram_id: int) -> bool:
        user = await self.col.find_one(
            {"telegram_id": telegram_id}, {"agreed": 1}
        )
        return bool(user and user.get("agreed"))

    async def mark_hint_seen(self, telegram_id: int, key: str) -> bool:
        result = await self.col.update_one(
            {"telegram_id": telegram_id, "seen_hints": {"$ne": key}},
            {"$addToSet": {"seen_hints": key}},
        )
        return result.modified_count == 1
    
    async def add_complaint(self, telegram_id: int) -> int:
        doc = await self.col.find_one_and_update(
            {"telegram_id": telegram_id},
            {"$inc": {"complaints": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return doc.get("complaints", 0)

    async def ban(self, telegram_id: int) -> None:
        await self.col.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"banned": True, "banned_at": datetime.utcnow()}},
            upsert=True,
        )

    async def is_banned(self, telegram_id: int) -> bool:
        doc = await self.col.find_one({"telegram_id": telegram_id}, {"banned": 1})
        return bool(doc and doc.get("banned"))

    async def get_by_username(self, username: str) -> dict | None:
        return await self.col.find_one({"username": username})