from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    role_in_band: Mapped[str] = mapped_column(String(100))
    photo_url: Mapped[str | None] = mapped_column(String(500), default=None)
    bio: Mapped[str | None] = mapped_column(Text, default=None)
    sns_links: Mapped[str | None] = mapped_column(Text, default=None)
    sort_order: Mapped[int] = mapped_column(default=0)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)

    user: Mapped[User | None] = relationship()
