from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

member_table = sa.table("member", sa.column("id", sa.BigInteger), sa.column("username", sa.String), sa.column("is_admin", sa.Boolean))


def upgrade() -> None:
    op.add_column(
        "member",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute(member_table.update().where(member_table.c.username == "henry").values(is_admin=True))


def downgrade() -> None:
    op.drop_column("member", "is_admin")
