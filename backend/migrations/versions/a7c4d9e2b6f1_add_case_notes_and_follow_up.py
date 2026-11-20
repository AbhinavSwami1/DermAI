"""add case clinical notes and follow-up date

Revision ID: a7c4d9e2b6f1
Revises: e93c9c1565a8
Create Date: 2026-11-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a7c4d9e2b6f1'
down_revision: Union[str, Sequence[str], None] = 'e93c9c1565a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('cases', sa.Column('clinical_notes', sa.Text(), nullable=True))
    op.add_column('cases', sa.Column('follow_up_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('cases', 'follow_up_date')
    op.drop_column('cases', 'clinical_notes')
