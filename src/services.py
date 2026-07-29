from models import UserModel
from sqlalchemy.ext.asyncio import AsyncSession
from schema import User, Facts
from sqlmodel import select, desc
from db_config import get_session
from dataclasses import dataclass
from redis.asyncio import Redis
from typing import List, Dict, TypedDict
from aiogram.types import Message
from buttons import description_about_self_button
from redis_config import UserInfoDict, get_user_info, store_user_info


class UpdatedDataDict(TypedDict):
    updated: bool | None
    user: User | None


class UserService:
    async def create_user(self, user_info: UserModel) -> User | None:
        async with get_session() as session:
            user_data = user_info.model_dump()
            new_user = User(**user_data)
            session.add(new_user)
            await session.flush()
        return new_user

    async def get_user_by_telegram_id(self, telegram_id: str):
        async with get_session() as session:
            statement = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(statement=statement)
            user = result.scalars().first()
        return user

    async def add_facts(self, telegram_id: str, fact: str):
        async with get_session() as session:
            new_fact = Facts(telegram_id=telegram_id, fact=fact)
            session.add(new_fact)
            await session.flush()
        return new_fact

    async def get_facts(self, telegram_id: str):
        async with get_session() as session:
            statement = (
                select(Facts)
                .where(Facts.telegram_id == telegram_id)
                .order_by(desc(Facts.created_at))
                .limit(20)
            )
            results = await session.execute(statement=statement)
            facts = results.scalars().all()
        return facts if len(facts) >= 1 else None

    async def update_info(
        self, telegram_id: str, info: Dict, message: Message
    ) -> UpdatedDataDict:
        return_message: UpdatedDataDict = {"updated": None, "user": None}
        async with get_session() as session:
            user = await self.get_user_by_telegram_id(telegram_id=telegram_id)
            if user is None:
                await message.answer(
                    "Please tell me more about yourself to continue our conversation",
                    reply_markup=description_about_self_button(),
                )
                return_message["updated"] = False
            else:
                user_info = await get_user_info(telegram_id=telegram_id)
                for key, value in info.items():
                    setattr(user, key, value)
                    if user_info is not None:
                        user_info[key] = value
                    else:
                        user_info: UserInfoDict = {
                            "companion_name": user.companion_name,
                            "companion_type": user.companion_type,
                            "ideal_description": user.ideal_description,
                            "user_description": user.user_description,
                            "user_name": user.user_name,
                        }
                return_message["updated"] = True
                return_message["user"] = user
                await store_user_info(telegram_id=telegram_id, user_info=user_info)
                await session.flush()
                await session.commit()

        return return_message


@dataclass(kw_only=True)
class GroqRateLimiter:
    redis_client: Redis
    max_per_minute: int = 25
    max_per_day: int = 900
    minute_key: str = "groq:rl:minute"
    day_key: str = "groq:rl:day"

    async def acquire(self) -> tuple[bool, str]:
        minute_count = await self.redis_client.get(self.minute_key)
        daily_count = await self.redis_client.get(self.day_key)
        minute_count = int(minute_count) if minute_count else 0
        daily_count = int(daily_count) if daily_count else 0
        if minute_count > self.max_per_minute:
            return (False, "minute")
        if daily_count > self.max_per_day:
            return (False, "daily")
        pipe = self.redis_client.pipeline()
        pipe.incr(self.minute_key)
        pipe.expire(self.minute_key, 60, nx=True)
        pipe.incr(self.day_key)
        pipe.expire(self.day_key, 86400, nx=True)
        await pipe.execute()
        return (True, "")

    async def seconds_until_minute(self) -> int:
        ttl = await self.redis_client.ttl(self.minute_key)
        return max(ttl, 1)
