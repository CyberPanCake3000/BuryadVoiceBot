import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database.mongo import Mongo
from handlers import start, suggest, voice, unknown, policy
from middlewares.agreement import AgreementMiddleware

try:
    import uvloop
    uvloop.install()
except ImportError:
    pass

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


async def main() -> None:
    mongo = Mongo(settings.mongo_uri, settings.mongo_db)
    await mongo.connect()
    await mongo.ensure_indexes()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage(), mongo=mongo)

    dp.message.middleware(AgreementMiddleware())

    dp.include_routers(
        start.router,
        suggest.router,
        voice.router,
        policy.router,
        unknown.router,
    )

    try:
        logger.info("Bot started")
        await dp.start_polling(bot)
    finally:
        await mongo.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())