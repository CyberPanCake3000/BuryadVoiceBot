from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def agreement_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, согласен(на)", callback_data="agree")],
    ])