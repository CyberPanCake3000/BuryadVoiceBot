from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def fill_translation_kb(doc_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Уже внесла / внёс",
            callback_data=f"ft:done:{doc_id}",
        )],
    ])