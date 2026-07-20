from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def suggest_voice_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Да, хочу озвучить", callback_data="sv:yes"),
        InlineKeyboardButton(text="❌ Нет, спасибо", callback_data="sv:no"),
    ]])