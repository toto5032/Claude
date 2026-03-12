from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    role: Mapped[str] = mapped_column(String(20), default="fan")
    display_name: Mapped[str | None] = mapped_column(String(255), default=None)
    bio: Mapped[str | None] = mapped_column(String(1000), default=None)
    avatar_url: Mapped[str | None] = mapped_column(String(500), default=None)
