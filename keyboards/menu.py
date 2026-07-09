from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_kb(role: str = "user") -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="/suggest"), KeyboardButton(text="/voice")],
    ]
    if role == "reviewer":
        rows.append([KeyboardButton(text="/startreview"), KeyboardButton(text="/translate")], [KeyboardButton(text="/cancel")])
    if role == "admin":
        rows.append([KeyboardButton(text="/addreviewer"), KeyboardButton(text="/addfortranslation")], [KeyboardButton(text="/cancel")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)