"""
Модель используемой анкеты.
"""
import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[Gender] = mapped_column(Enum(Gender))
    looking_for: Mapped[Gender] = mapped_column(Enum(Gender))
    city: Mapped[str] = mapped_column(String(128))
    bio_text: Mapped[str] = mapped_column(Text)
    photo_file_id: Mapped[str] = mapped_column(String(256))
    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
