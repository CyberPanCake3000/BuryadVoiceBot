from config import settings
from database.mongo import Mongo
from database.repositories.reviewers import ReviewersRepository


async def get_role(telegram_id: int, mongo: Mongo) -> str:
    if telegram_id in settings.admin_ids:
        return "admin"
    reviewers = ReviewersRepository(mongo.db)
    if await reviewers.is_reviewer(telegram_id):
        return "reviewer"
    return "user"