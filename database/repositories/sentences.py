from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from database.models import SentenceStatus
from config import settings


class SentencesRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db.suggested_sentences

    async def add(self, text: str, author: int) -> None:
        result = await self.col.insert_one({
            "text": text,
            "source": "telegram",
            "author": author,
            "status": SentenceStatus.PENDING,
            "moderator": None,
            "reviews": [],
            "approved_at": None,
            "created_at": datetime.utcnow(),
        })
        return result.inserted_id

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

    async def random_unreviewed(self, reviewer_id: int, limit: int = 5) -> list[dict]:
        cursor = self.col.aggregate([
            {"$match": {
                "status": SentenceStatus.PENDING,
                "reviews.reviewer_id": {"$ne": reviewer_id}, 
            }},
            {"$sample": {"size": limit}},
        ])
        return [doc async for doc in cursor]

    async def add_review(self, doc_id, reviewer_id: int, decision: str) -> bool:
        result = await self.col.update_one(
            {"_id": doc_id, "reviews.reviewer_id": {"$ne": reviewer_id}},
            {"$push": {"reviews": {
                "reviewer_id": reviewer_id,
                "decision": decision,
                "created_at": datetime.utcnow(),
            }}},
        )
        return result.modified_count == 1

    from config import settings

    async def recalc_status(self, doc_id) -> str | None:
        doc = await self.col.find_one({"_id": doc_id}, {"reviews": 1, "status": 1})
        if doc is None:
            return None

        reviews = doc.get("reviews", [])
        approvals = sum(1 for r in reviews if r["decision"] == "approve")
        rejections = sum(1 for r in reviews if r["decision"] == "reject")
        threshold = settings.approval_threshold

        new_status = None
        if approvals >= threshold and approvals > rejections:
            new_status = SentenceStatus.APPROVED
        elif rejections >= threshold and rejections > approvals:
            new_status = SentenceStatus.REJECTED

        old_status = doc.get("status")
        if new_status and new_status != old_status:
            update = {"status": new_status}
            if new_status in (SentenceStatus.APPROVED, SentenceStatus.REJECTED):
                update["approved_at"] = datetime.utcnow()
            await self.col.update_one({"_id": doc_id}, {"$set": update})
            return new_status

        if old_status != SentenceStatus.PENDING and new_status is None:
            await self.col.update_one(
                {"_id": doc_id},
                {"$set": {"status": SentenceStatus.PENDING}, "$unset": {"approved_at": ""}},
            )
            return SentenceStatus.PENDING

        return None

    async def get_author(self, doc_id) -> int | None:
        doc = await self.col.find_one({"_id": doc_id}, {"author": 1})
        return doc["author"] if doc else None

    async def update_text(self, doc_id, new_text: str) -> bool:
        result = await self.col.update_one(
            {"_id": doc_id},
            {"$set": {"text": new_text}},
        )
        return result.modified_count == 1

    async def add_edit_review(self, doc_id, reviewer_id: int, edited_text: str) -> bool:
        result = await self.col.update_one(
            {"_id": doc_id, "reviews.reviewer_id": {"$ne": reviewer_id}},
            {
                "$set": {"text": edited_text},
                "$push": {"reviews": {
                    "reviewer_id": reviewer_id,
                    "decision": "edit",
                    "edited_text": edited_text,
                    "created_at": datetime.utcnow(),
                }},
            },
        )
        return result.modified_count == 1