from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_button(text: str, callback_data):
    builder = InlineKeyboardBuilder()
    builder.button(text=text, callback_data=callback_data)
    return builder.as_markup


def companion_type_buttons():
    buttons = []
    builder = InlineKeyboardBuilder()
    boyfriend_button = InlineKeyboardButton(
        text="Boyfriend 👦", callback_data="boyfriend"
    )
    buttons.append(boyfriend_button)
    girlfriend_button = InlineKeyboardButton(
        text="Girlfriend 👧", callback_data="girlfriend"
    )
    buttons.append(girlfriend_button)
    builder.add(*buttons)
    return builder.as_markup()


description_about_self_button = create_button(
    text="Tell me about yourself 😊".title(), callback_data="self_description"
)
companion_type_buttons = companion_type_buttons()
