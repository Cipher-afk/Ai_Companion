from aiogram import Bot, Dispatcher, Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import settings
from aiogram.filters import Command
from buttons import (
    description_about_self_button,
    companion_type_buttons,
    edit_info_buttons,
    create_button,
)
from services import UserService, GroqRateLimiter
from models import UserModel
from redis_config import UserInfoDict
from schema import User
from redis_config import (
    store_user_info,
    get_user_info,
    add_messages,
    get_messages,
    redis_client,
)
import json
from ai import edit_prompt, get_ai_response, call_groq_with_retry
from typing import List, Dict
from db_config import init_db
import asyncio

bot = Bot(settings.BOT_TOKEN)
dp = Dispatcher()
router = Router()
user_service = UserService()
groq_limiter = GroqRateLimiter(redis_client=redis_client)


class SelfDescriptionState(StatesGroup):
    user_name = State()
    companion_type = State()
    companion_name = State()
    user_description = State()
    ideal_description = State()


@router.message(Command("start"))
async def start_bot(message: Message):
    await message.answer(
        "Hello My Love 💖 it's nice seeing you today\nI would love to know more about you if you dont't mind 😊",
        reply_markup=description_about_self_button(),
    )


@router.callback_query(F.data == "self_description")
async def self_description(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Can i please get your name dear 😇")
    await state.set_state(SelfDescriptionState.user_name)


@router.message(SelfDescriptionState.user_name)
async def set_username(message: Message, state: FSMContext):
    username = message.text
    await state.update_data(user_name=username)
    await message.answer(
        f"Hello {username} do you want a".title(), reply_markup=companion_type_buttons
    )
    await state.set_state(SelfDescriptionState.companion_type)


@router.callback_query(F.data == "boyfriend")
async def store_boyfriend(callback: CallbackQuery, state: FSMContext):
    await state.update_data(companion_type="boyfriend")
    await callback.message.answer(
        "Well dear what name would you love to call me 😊".title()
    )
    await state.set_state(SelfDescriptionState.companion_name)


@router.callback_query(F.data == "girlfriend")
async def store_girlfriend(callback: CallbackQuery, state: FSMContext):
    await state.update_data(companion_type="girlfriend")
    await callback.message.answer(
        "Well dear what name would you love to call me 😊".title()
    )
    await state.set_state(SelfDescriptionState.companion_name)


@router.message(SelfDescriptionState.companion_name)
async def store_companion_name(message: Message, state: FSMContext):
    companion_name = message.text
    await state.update_data(companion_name=companion_name)
    await message.answer(
        f"Hmmm {companion_name}\nI Love it 😚💓 Can you please tell me more about yourself 🥺💖"
    )
    await state.set_state(SelfDescriptionState.user_description)


@router.message(SelfDescriptionState.user_description)
async def store_users_description(message: Message, state: FSMContext):
    await state.update_data(user_description=message.text)
    data = await state.get_data()
    companion_type = data.get("companion_type")
    await message.answer(
        f"Wow you sound really nice 😋\nCan't wait to learn more about you but before that if i may ask what's your ideal type of {companion_type}"
    )
    await state.set_state(SelfDescriptionState.ideal_description)


@router.message(SelfDescriptionState.ideal_description)
async def store_ideal_type(message: Message, state: FSMContext):
    data = await state.get_data()
    telegram_id = str(message.chat.id)
    ideal_type = message.text
    data["ideal_description"] = ideal_type
    data["telegram_id"] = telegram_id
    user_info = UserModel(**data)
    await state.clear()
    new_user: User = await user_service.create_user(user_info=user_info)
    user_info: UserInfoDict = {
        "user_name": new_user.user_name,
        "companion_name": new_user.companion_name,
        "ideal_description": new_user.ideal_description,
        "user_description": new_user.user_description,
        "companion_type": new_user.companion_type,
    }
    await store_user_info(telegram_id=telegram_id, user_info=user_info)
    message_ = f"""
Hello {new_user.user_name} 👋
My name is {new_user.companion_name} 😊 It's a pleasure to meet you 😘"""

    await message.answer(message_)
    await add_messages(
        telegram_id=telegram_id, role=new_user.companion_name, content=message_
    )


@router.message(Command("edit_info"))
async def edit_info(message: Message):
    await message.answer(
        "Which Part of me do you want to change love 💖".title(),
        reply_markup=edit_info_buttons,
    )


@router.callback_query(F.data == "edit_user_name")
async def edit_user_name(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("What new name should i call you now dear 😊")
    await state.set_state(SelfDescriptionState.user_name)


@router.message(SelfDescriptionState.user_name)
async def update_user_name(message: Message, state: FSMContext):
    user_name = message.text
    telegram_id = str(message.chat.id)
    info = {"user_name": user_name}
    updated_data = await user_service.update_info(
        telegram_id=telegram_id, info=info, message=message
    )
    updated = updated_data["updated"]
    user = updated_data["user"]
    if updated:
        message_ = f"Ok from now on i'll call you {user_name} 😌 so {user_name} what are you up to??"
        await state.clear()
        await message.answer(message_)
        await add_messages(
            telegram_id=telegram_id, role=user.companion_name, content=message
        )
    else:
        await state.clear()
        await message.answer(
            "Sorry Something went wrong on my end please try again",
            reply_markup=create_button(
                text="Edit Your Name ✏", callback_data="edit_user_name"
            ),
        )


@router.callback_query(F.data == "edit_companion_name")
async def edit_companion_name(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("What do you want to call me now love 🥺")
    await state.set_state(SelfDescriptionState.companion_name)


@router.message(SelfDescriptionState.companion_name)
async def update_user_name(message: Message, state: FSMContext):
    companion_name = message.text
    telegram_id = str(message.chat.id)
    info = {"companion_name": companion_name}
    updated_data = await user_service.update_info(
        telegram_id=telegram_id, info=info, message=message
    )
    updated = updated_data["updated"]
    user = updated_data["user"]
    if updated:
        message_ = f"Hmmm {companion_name} 😏 huh\nGuess that's my name now 😏"
        await state.clear()
        await message.answer(message_)
        await add_messages(
            telegram_id=telegram_id, role=companion_name, content=message
        )
    else:
        await state.clear()
        await message.answer(
            "Sorry Something went wrong on my end please try again",
            reply_markup=create_button(
                text="Edit My Name ✏", callback_data="edit_companion_name"
            ),
        )


@router.callback_query(F.data == "edit_user_character")
async def edit_user_character(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Hit me with it.\nWhat's your new character? 😏")
    await state.set_state(SelfDescriptionState.user_description)


@router.message(SelfDescriptionState.user_description)
async def update_user_name(message: Message, state: FSMContext):
    user_description = message.text
    telegram_id = str(message.chat.id)
    info = {"user_description": user_description}
    updated_data = await user_service.update_info(
        telegram_id=telegram_id, info=info, message=message
    )
    updated = updated_data["updated"]
    user = updated_data["user"]
    if updated:
        message_ = f"Ooh, i wasn't expecting that! I actually love it. Now i'm excited to see you bring it to life. ✨😊"
        await state.clear()
        await message.answer(message_)
        await add_messages(
            telegram_id=telegram_id, role=user.companion_name, content=message
        )
    else:
        await state.clear()
        await message.answer(
            "Sorry Something went wrong on my end please try again",
            reply_markup=create_button(
                "Edit Your Character ✏", callback_data="edit_user_character"
            ),
        )


@router.callback_query(F.data == "edit_companion_character")
async def edit_companion_name(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "Want to change my personality?\nAlright then... what kind of companion would you like me to be?💖"
    )
    await state.set_state(SelfDescriptionState.ideal_description)


@router.message(SelfDescriptionState.ideal_description)
async def update_user_name(message: Message, state: FSMContext):
    ideal_description = message.text
    telegram_id = str(message.chat.id)
    info = {"ideal_description": ideal_description}
    updated_data = await user_service.update_info(
        telegram_id=telegram_id, info=info, message=message
    )
    updated = updated_data["updated"]
    user = updated_data["user"]
    if updated:
        message_ = f"I like that choice. I'll do my beat to be that kind of companion for you. Just be patient if i slip up every now and then. 🤍"
        await state.clear()
        await message.answer(message_)
        await add_messages(
            telegram_id=telegram_id, role=user.companion_name, content=message
        )
    else:
        await state.clear()
        await message.answer(
            "Sorry Something went wrong on my end please try again",
            reply_markup=create_button(
                text="Edit My Character ✏", callback_data="edit_companion_character"
            ),
        )


@router.message(F.text)
async def handle_responses(message: Message):
    telegram_id = str(message.chat.id)
    await message.answer("Typing....")
    user_info = await get_user_info(telegram_id=telegram_id)
    print(user_info)
    if not user_info:
        user: User | None = await user_service.get_user_by_telegram_id(telegram_id)
        if user is None:
            await message.answer(
                "Please tell me more about yourself to continue our conversation",
                reply_markup=description_about_self_button(),
            )
            return

        user_info: UserInfoDict = {
            "companion_name": user.companion_name,
            "companion_type": user.companion_type,
            "ideal_description": user.ideal_description,
            "user_description": new_user.user_description,
            "user_name": user.user_name,
        }
    facts = await user_service.get_facts(telegram_id)
    edited_facts = None if facts is None else [fact.fact for fact in facts]
    previous_conversations = await get_messages(telegram_id=telegram_id)
    edited_previous_conversations = [
        json.dumps({conversation["role"]: conversation["content"]})
        for conversation in previous_conversations
    ]
    new_incoming_message = message.text
    new_prompt = edit_prompt(
        user_info=user_info,
        previous_conversations=edited_previous_conversations,
        new_incoming_message=new_incoming_message,
        facts=edited_facts,
    )
    allowed, reason = await groq_limiter.acquire()
    if not allowed:
        if reason == "minute":
            wait = await groq_limiter.seconds_until_minute()
            await message.answer(
                f"Give me about {wait}s, back in a bit love 😘 don't miss me too much 😏"
            )
        else:
            await message.answer(
                "I still really want to talk with you 🥺 but unfortunately i've hit my limit for the day 😭"
            )
        return
    try:
        response: Dict = await call_groq_with_retry(prompt=new_prompt)
        # print(response)
        response_facts: List[str] = response["facts"]
        number_of_facts = len(response_facts)
        if number_of_facts >= 1:
            for i in range(number_of_facts):
                await user_service.add_facts(telegram_id=telegram_id, fact=facts[i])
        response_reply: str = response["reply"]
        await message.answer(response_reply)
        await add_messages(
            telegram_id=telegram_id,
            role=user_info["user_name"],
            content=new_incoming_message,
        )
        await add_messages(
            telegram_id=telegram_id,
            role=user_info["companion_name"],
            content=response_reply,
        )
    except Exception as e:
        await message.answer("Something broke on my end, try again in a bit")
        print(f"Groq_Error: {e}", flush=True)


async def main():
    await init_db()
    print("DB initialized")
    dp.include_router(router=router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    print("Started...")
    asyncio.run(main())
