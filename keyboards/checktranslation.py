from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def check_translation_kb(doc_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Хороший перевод", callback_data=f"ct:approve:{doc_id}"),
            InlineKeyboardButton(text="✏️ Исправить", callback_data=f"ct:edit:{doc_id}"),
        ],
        [
            InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"ct:skip:{doc_id}"),
        ],
    ])