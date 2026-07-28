from redis.asyncio import Redis
from config import settings
import json
from typing import TypedDict, List, Dict

redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
)


class UserInfoDict(TypedDict):
    companion_name: str
    user_name: str
    companion_type: str
    ideal_description: str
    user_description: str


async def store_user_info(telegram_id: str, user_info: UserInfoDict):
    name = f"chat:{telegram_id}"
    await redis_client.hset(name=name, mapping=user_info)


async def get_user_info(telegram_id: str):
    name = f"chat:{telegram_id}"
    user_data = await redis_client.hgetall(name=name)
    return user_data


async def add_messages(telegram_id: str, role: str, content: str):
    name = f"converstion:{telegram_id}"
    entry = json.dumps({"role": role, "content": content})
    await redis_client.rpush(name, entry)
    await redis_client.ltrim(name, -15, -1)


async def get_messages(telegram_id: str):
    name = f"converstion:{telegram_id}"
    raw_data = await redis_client.lrange(name, 0, -1)
    messages: List[Dict] = [json.loads(data) for data in raw_data]
    return messages
