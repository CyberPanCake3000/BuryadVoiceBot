from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from database.models import SentenceStatus


class VoicesRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db.voice_records

    async def add(
        self,
        sentence_id,
        telegram_id: int,
        file_id: str,
        unique_id: str,
        duration: int | None,
    ) -> None:
        await self.col.insert_one({
            "sentence_id": sentence_id,
            "telegram_id": telegram_id,
            "telegram_file_id": file_id,
            "telegram_unique_id": unique_id,
            "duration": duration,
            "status": SentenceStatus.PENDING,
            "created_at": datetime.utcnow(),
        })