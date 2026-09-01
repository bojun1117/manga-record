import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.model.base import Base


class ReadingStatus(str, enum.Enum):
    """DATA_MODEL.md 的四個追讀狀態。"""

    PLAN_TO_READ = "plan_to_read"
    READING = "reading"
    DROPPED = "dropped"
    COMPLETED = "completed"


class MemberManga(Base):
    """DATA_MODEL.md `member_manga`。表名用標準關聯表命名法，API 路徑仍叫 /collections。

    rating 不綁定 status（跟舊系統 comic-vibe 不同的簡化決策，見 API.md 驗證規則）。
    """

    __tablename__ = "member_manga"
    __table_args__ = (
        UniqueConstraint("member_id", "manga_id", name="uq_member_manga_member_id_manga_id"),
        CheckConstraint(
            "current_volume IS NULL OR current_volume >= 0",
            name="ck_member_manga_current_volume_non_negative",
        ),
        CheckConstraint(
            "current_chapter IS NULL OR current_chapter >= 0",
            name="ck_member_manga_current_chapter_non_negative",
        ),
        CheckConstraint(
            "rating IS NULL OR (rating BETWEEN 1 AND 5)",
            name="ck_member_manga_rating_range",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("member.id", ondelete="CASCADE"), nullable=False
    )
    manga_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("manga.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[ReadingStatus] = mapped_column(
        Enum(ReadingStatus, name="reading_status", native_enum=True, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=ReadingStatus.PLAN_TO_READ,
    )
    current_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_chapter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
