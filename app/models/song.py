from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    artist: Mapped[str] = mapped_column(String(255))
    youtube_url: Mapped[str] = mapped_column(String(500))
    youtube_video_id: Mapped[str] = mapped_column(String(20))
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), default=None)
    genre: Mapped[str | None] = mapped_column(String(100), default=None)
    status: Mapped[str] = mapped_column(String(20), default="candidate")
    reason: Mapped[str | None] = mapped_column(Text, default=None)
    suggested_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    suggested_by: Mapped[User | None] = relationship()
    votes: Mapped[list[SongVote]] = relationship(back_populates="song")
    fan_votes: Mapped[list[SongFanVote]] = relationship(back_populates="song")
    comments: Mapped[list[SongComment]] = relationship(back_populates="song")


class SongVote(Base):
    __tablename__ = "song_votes"
    __table_args__ = (UniqueConstraint("song_id", "user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    song_id: Mapped[int] = mapped_column(ForeignKey("songs.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    vote_type: Mapped[str] = mapped_column(String(10), default="up")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    song: Mapped[Song] = relationship(back_populates="votes")
    user: Mapped[User] = relationship()


class SongFanVote(Base):
    __tablename__ = "song_fan_votes"
    __table_args__ = (UniqueConstraint("song_id", "user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    song_id: Mapped[int] = mapped_column(ForeignKey("songs.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    song: Mapped[Song] = relationship(back_populates="fan_votes")
    user: Mapped[User] = relationship()


class SongComment(Base):
    __tablename__ = "song_comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    song_id: Mapped[int] = mapped_column(ForeignKey("songs.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    song: Mapped[Song] = relationship(back_populates="comments")
    user: Mapped[User] = relationship()
