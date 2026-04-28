from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    telegram_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_authorized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    invite_code_id: Mapped[int | None] = mapped_column(
        ForeignKey("invite_codes.id", ondelete="SET NULL"),
        nullable=True,
    )

    invite_code = relationship("InviteCode", back_populates="users")
    reports = relationship("Report", back_populates="author")
