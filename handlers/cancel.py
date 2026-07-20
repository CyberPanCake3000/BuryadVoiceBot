from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram import F

from database.mongo import Mongo

router = Router(name="cancel")


@router.message(Command("cancel"))
@router.message(F.text == "Отменить")
async def cmd_cancel(message: Message, state: FSMContext, mongo: Mongo) -> None:
    current = await state.get_state()

    if current == "FillTranslationState:ACTIVE":
        await state.clear()
        await message.answer("Внесение переводов отменено.")
        return

    if current == "CheckTranslationState:WAIT_EDIT":
        await state.set_state("CheckTranslationState:ACTIVE")
        await message.answer("Исправление отменено.")
        from handlers.checktranslation import send_next_item
        await send_next_item(message, state, mongo)
        return

    if current == "CheckTranslationState:ACTIVE":
        await state.clear()
        await message.answer("Проверка переводов отменена.")
        return

    if current == "ReviewState:WAIT_EDIT":
        await state.clear()
        await message.answer("Исправление отменено. Вот следующая фраза.")
        from handlers.startreview import send_next_sentence
        await send_next_sentence(message, message.from_user.id, mongo)
        return

    if current is None:
        await message.answer("Сейчас нечего отменять.")
        return

    await state.clear()
    await message.answer("Действие отменено.")