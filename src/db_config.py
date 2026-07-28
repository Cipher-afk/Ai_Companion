from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import settings
from sqlmodel import SQLModel
from contextlib import asynccontextmanager

url = settings.DATABASE_URL
engine = create_async_engine(url=url, echo=True)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async_session: sessionmaker[AsyncSession] = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@asynccontextmanager
async def get_session():
    try:
        async with async_session() as session:
            yield session
            await session.commit()
    except Exception as e:
        print(e, flush=True)
        await session.rollback()
