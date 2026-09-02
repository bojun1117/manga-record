from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


manga_category = postgresql.ENUM(
    "hot_blooded",
    "mystery",
    "adventure",
    "romance",
    "casual",
    "competition",
    "revenge",
    "slice_of_life",
    "other",
    name="manga_category",
    create_type=False,
)

reading_status = postgresql.ENUM(
    "plan_to_read",
    "reading",
    "dropped",
    "completed",
    name="reading_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    manga_category.create(bind, checkfirst=True)
    reading_status.create(bind, checkfirst=True)

    op.create_table(
        "member",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(30), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("username", name="uq_member_username"),
    )

    op.create_table(
        "manga",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("normalized_title", sa.String(200), nullable=False),
        sa.Column("category", manga_category, nullable=False, server_default="other"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("normalized_title", name="uq_manga_normalized_title"),
    )

    op.create_table(
        "member_manga",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "member_id",
            sa.BigInteger(),
            sa.ForeignKey("member.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "manga_id",
            sa.BigInteger(),
            sa.ForeignKey("manga.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", reading_status, nullable=False, server_default="plan_to_read"),
        sa.Column("current_volume", sa.Integer(), nullable=True),
        sa.Column("current_chapter", sa.Integer(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("last_read_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("member_id", "manga_id", name="uq_member_manga_member_id_manga_id"),
        sa.CheckConstraint(
            "current_volume IS NULL OR current_volume >= 0",
            name="ck_member_manga_current_volume_non_negative",
        ),
        sa.CheckConstraint(
            "current_chapter IS NULL OR current_chapter >= 0",
            name="ck_member_manga_current_chapter_non_negative",
        ),
        sa.CheckConstraint(
            "rating IS NULL OR (rating BETWEEN 1 AND 5)",
            name="ck_member_manga_rating_range",
        ),
    )


def downgrade() -> None:
    op.drop_table("member_manga")
    op.drop_table("manga")
    op.drop_table("member")
    reading_status.drop(op.get_bind(), checkfirst=True)
    manga_category.drop(op.get_bind(), checkfirst=True)
