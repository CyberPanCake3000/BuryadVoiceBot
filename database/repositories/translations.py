from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase


class NeedTranslationRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db.need_translation

    async def random_unseen(self, reviewer_id: int, limit: int = 3) -> list[dict]:
        """pending + этот ревьюер ещё не в reviews[]"""
        cursor = self.col.aggregate([
            {"$match": {
                "status": "pending",
                "reviews.reviewer_id": {"$ne": reviewer_id},
            }},
            {"$sample": {"size": limit}},
        ])
        return [doc async for doc in cursor]

    async def _record_review(self, doc_id, reviewer_id: int, decision: str, extra: dict | None = None) -> bool:
        update = {
            "$push": {"reviews": {
                "reviewer_id": reviewer_id,
                "decision": decision,
                "created_at": datetime.utcnow(),
            }},
            "$set": {"updated_at": datetime.utcnow()},
        }
        if extra:
            update["$set"].update(extra)
        result = await self.col.update_one(
            {"_id": doc_id, "status": "pending", "reviews.reviewer_id": {"$ne": reviewer_id}},
            update,
        )
        return result.modified_count == 1

    async def approve(self, doc_id, reviewer_id: int) -> bool:
        return await self._record_review(doc_id, reviewer_id, "approve", {
            "status": "approved",
            "reviewed_by": reviewer_id,
            "reviewed_at": datetime.utcnow(),
        })

    async def skip(self, doc_id, reviewer_id: int) -> bool:
        return await self._record_review(doc_id, reviewer_id, "skip")

    async def approve_edited(
        self, doc_id, reviewer_id: int, translation: str, mt_draft: str
    ) -> bool:
        edited = translation.strip() != mt_draft.strip()
        return await self._record_review(doc_id, reviewer_id, "edit", {
            "translation": translation.strip(),
            "edited": edited,
            "status": "approved",
            "reviewed_by": reviewer_id,
            "reviewed_at": datetime.utcnow(),
        })

    async def random_approved(self, limit: int = 3) -> list[dict]:
        cursor = self.col.aggregate([
            {"$match": {"status": "approved"}},
            {"$sample": {"size": limit}},
        ])
        return [doc async for doc in cursor]

    async def mark_recorded(self, doc_id, admin_id: int) -> bool:
        result = await self.col.update_one(
            {"_id": doc_id, "status": "approved"},
            {"$set": {
                "status": "recorded",
                "recorded_by": admin_id,
                "recorded_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }},
        )
        return result.modified_count == 1