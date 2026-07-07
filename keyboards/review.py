from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def review_kb(sentence_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Принять",   callback_data=f"rv:approve:{sentence_id}"),
        InlineKeyboardButton(text="❌ Отклонить",  callback_data=f"rv:reject:{sentence_id}"),
        InlineKeyboardButton(text="🚫 Пожаловаться", callback_data=f"rv:complain:{sentence_id}"),
    ]])