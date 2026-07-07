"""add pairing_email to cameras

Revision ID: cfb90e417b97
Revises: 2b1c2f54ea78
Create Date: 2026-07-07 00:34:18.229279

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'cfb90e417b97'
down_revision: Union[str, None] = '2b1c2f54ea78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('cameras', sa.Column('pairing_email', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('cameras', 'pairing_email')
