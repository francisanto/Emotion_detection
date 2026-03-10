"""SQLAlchemy ORM models for users, conversations, and relationship metrics."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    messages_sent: Mapped[list["Message"]] = relationship(
        back_populates="sender",
        cascade="all, delete",
        passive_deletes=True,
    )

    conversations_as_a: Mapped[list["Conversation"]] = relationship(
        back_populates="person_a",
        foreign_keys="Conversation.person_a_id",
        cascade="all, delete",
        passive_deletes=True,
    )
    conversations_as_b: Mapped[list["Conversation"]] = relationship(
        back_populates="person_b",
        foreign_keys="Conversation.person_b_id",
        cascade="all, delete",
        passive_deletes=True,
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_a_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    person_b_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    person_a: Mapped["User"] = relationship(
        back_populates="conversations_as_a",
        foreign_keys=[person_a_id],
    )
    person_b: Mapped["User"] = relationship(
        back_populates="conversations_as_b",
        foreign_keys=[person_b_id],
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete",
        passive_deletes=True,
        order_by="Message.timestamp",
    )

    daily_metrics: Mapped[list["DailyRelationshipMetrics"]] = relationship(
        back_populates="conversation",
        cascade="all, delete",
        passive_deletes=True,
        order_by="DailyRelationshipMetrics.date",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    emotion: Mapped[str] = mapped_column(String(64), nullable=False, default="neutral")
    emotion_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship(back_populates="messages_sent")


class DailyRelationshipMetrics(Base):
    __tablename__ = "daily_relationship_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    positive_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    negative_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    affection_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="daily_metrics")

