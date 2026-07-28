from models import UserModel
from sqlalchemy.ext.asyncio import AsyncSession
from schema import User, Facts
from sqlmodel import select, desc
from db_config import get_session


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
