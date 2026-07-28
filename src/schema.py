from sqlmodel import SQLModel, Field, Column
import uuid
from uuid import UUID
from datetime import datetime
import sqlalchemy.dialects.postgresql as pg


class User(SQLModel, table=True):
    __tablename__ = "user"
    user_id: UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(pg.UUID, unique=True, nullable=False, primary_key=True),
    )
    telegram_id: str = Field(
        sa_column=Column(pg.VARCHAR, nullable=False, index=True, unique=True)
    )
    user_name: str
    companion_type: str
    companion_name: str
    user_description: str
    ideal_description: str
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())


class Facts(SQLModel, table=True):
    fact_id: UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(pg.UUID, unique=True, nullable=False, primary_key=True),
    )
    telegram_id: str = Field(foreign_key="user.telegram_id")
    fact: str
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
