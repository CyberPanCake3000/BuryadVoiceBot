from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def agreement_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Согласен", callback_data="agree")],
    ])