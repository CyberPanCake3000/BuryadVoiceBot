from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/translate"), KeyboardButton(text="/suggest")],
            [KeyboardButton(text="/voice"), KeyboardButton(text="/stats")],
        ],
        resize_keyboard=True,
    )