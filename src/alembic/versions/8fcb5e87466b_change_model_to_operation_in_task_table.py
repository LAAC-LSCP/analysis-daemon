"""change model to operation in task table

Revision ID: 8fcb5e87466b
Revises: 20ad0d336c6c
Create Date: 2025-11-02 23:07:34.940576

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8fcb5e87466b"
down_revision: Union[str, Sequence[str], None] = "20ad0d336c6c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "tasks",
        column_name="model",
        new_column_name="operation",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "tasks",
        column_name="operation",
        new_column_name="model",
    )
