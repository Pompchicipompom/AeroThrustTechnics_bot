from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ReportStatus, SubmitMode


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    submit_mode: Mapped[SubmitMode] = mapped_column(
        Enum(
            SubmitMode,
            name="submit_mode_enum",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    zone: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(
            ReportStatus,
            name="report_status_enum",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=ReportStatus.NEW,
        server_default=text("'new'"),
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    author = relationship("User", back_populates="reports")
    attachments = relationship("Attachment", back_populates="report")
