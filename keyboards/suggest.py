from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def suggest_voice_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Да", callback_data="sv:yes"),
        InlineKeyboardButton(text="❌ Нет", callback_data="sv:no"),
    ]])