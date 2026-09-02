from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.core.chinese import to_traditional

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


manga_table = sa.table("manga", sa.column("id", sa.BigInteger), sa.column("title", sa.String))


def upgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.select(manga_table.c.id, manga_table.c.title)).fetchall()
    for row in rows:
        converted = to_traditional(row.title)
        if converted != row.title:
            bind.execute(
                manga_table.update().where(manga_table.c.id == row.id).values(title=converted)
            )


def downgrade() -> None:
    pass
