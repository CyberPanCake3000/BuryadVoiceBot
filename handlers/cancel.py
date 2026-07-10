from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.mongo import Mongo

router = Router(name="cancel")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, mongo: Mongo) -> None:
    current = await state.get_state()

    if current == "ReviewState:WAIT_EDIT":
        await state.clear()
        await message.answer("Редактирование отменено. Показываю следующее предложение.")
        from handlers.startreview import send_next_sentence
        await send_next_sentence(message, message.from_user.id, mongo)
        return

    if current is None:
        await message.answer("Сейчас нечего отменять 🙂")
        return

    await state.clear()
    await message.answer("Действие отменено 👌")