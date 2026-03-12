from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.song import Song
    from app.models.user import User


class Show(Base):
    __tablename__ = "shows"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    venue: Mapped[str] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(500), default=None)
    show_date: Mapped[date] = mapped_column(Date)
    show_time: Mapped[time | None] = mapped_column(Time, default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    ticket_url: Mapped[str | None] = mapped_column(String(500), default=None)
    ticket_price: Mapped[str | None] = mapped_column(String(100), default=None)
    poster_url: Mapped[str | None] = mapped_column(String(500), default=None)
    status: Mapped[str] = mapped_column(String(20), default="upcoming")
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    created_by: Mapped[User | None] = relationship()
    setlist_items: Mapped[list[SetlistItem]] = relationship(
        back_populates="show", order_by="SetlistItem.play_order"
    )


class SetlistItem(Base):
    __tablename__ = "setlist_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    show_id: Mapped[int] = mapped_column(ForeignKey("shows.id", ondelete="CASCADE"))
    song_id: Mapped[int] = mapped_column(ForeignKey("songs.id", ondelete="CASCADE"))
    play_order: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(String(255), default=None)

    show: Mapped[Show] = relationship(back_populates="setlist_items")
    song: Mapped[Song] = relationship()
