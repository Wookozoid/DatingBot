"""
Модель используемой анкеты.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger, DateTime, Enum, ForeignKey, Integer, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"


class InteractionType(str, enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"


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


class Interaction(Base):
    """
    Лайк или дизлайк одного пользователя по отношению к другому
    """
    __tablename__ = "interactions"
    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", name="uq_interaction_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    to_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    type: Mapped[InteractionType] = mapped_column(Enum(InteractionType))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Match(Base):
    """
    Запись создается автоматически, когда лайк оказывается взаимным
    """
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("user_a_id", "user_b_id", name="uq_match_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_a_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    user_b_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    