"""add camera_id to schedules

Revision ID: 4949d8cb1491
Revises: 0907b88cc740
Create Date: 2026-07-06 19:07:25.724026

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4949d8cb1491'
down_revision: Union[str, None] = '0907b88cc740'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('schedules', sa.Column('camera_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_schedules_camera_id_cameras',
        'schedules', 'cameras', ['camera_id'], ['id'], ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_schedules_camera_id_cameras', 'schedules', type_='foreignkey')
    op.drop_column('schedules', 'camera_id')
