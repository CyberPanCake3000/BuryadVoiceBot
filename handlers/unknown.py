from aiogram import Router
from aiogram.types import Message

router = Router(name="unknown")


@router.message()
async def unknown_message(message: Message) -> None:
    await message.answer(
        "Не поняла эту команду.\n"
        "Воспользуйтесь кнопками внизу экрана "
        "или напишите /start"
    )