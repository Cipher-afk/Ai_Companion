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


def make_changes_buttons():
    buttons = []
    builder = InlineKeyboardBuilder()
    user_name = InlineKeyboardButton(
        text="Edit Your Name ✏", callback_data="edit_user_name"
    )
    buttons.append(user_name)
    companion_name = InlineKeyboardButton(
        text="Edit My Name ✏", callback_data="edit_companion_name"
    )
    buttons.append(companion_name)
    user_description = InlineKeyboardButton(
        text="Edit Your Character ✏", callback_data="edit_user_character"
    )
    buttons.append(user_description)
    companion_description = InlineKeyboardButton(
        text="Edit My Character ✏", callback_data="edit_companion_character"
    )
    buttons.append(companion_description)
    builder.add(*buttons)
    builder.adjust(2, 2)
    return builder.as_markup()


description_about_self_button = create_button(
    text="Tell me about yourself 😊".title(), callback_data="self_description"
)
companion_type_buttons = companion_type_buttons()
edit_info_buttons = make_changes_buttons()
