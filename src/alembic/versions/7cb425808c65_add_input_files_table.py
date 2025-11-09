"""add input_files table

Revision ID: 7cb425808c65
Revises: 5ed6a90fad8f
Create Date: 2025-11-09 23:30:16.583527

"""

from typing import Sequence, Union

import sqlalchemy as sa

import src.adapters.orm
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7cb425808c65"
down_revision: Union[str, Sequence[str], None] = "5ed6a90fad8f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "input_files",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("file_path", src.adapters.orm.PathType(length=256), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(
            sa.Column(
                "input_folder", src.adapters.orm.PathType(length=256), nullable=False
            )
        )
        batch_op.alter_column("operation", existing_type=sa.VARCHAR(), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.alter_column("operation", existing_type=sa.VARCHAR(), nullable=True)
        batch_op.drop_column("input_folder")

    op.drop_table("input_files")
