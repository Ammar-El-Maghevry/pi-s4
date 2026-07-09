"""add class_name to students and schedules

Revision ID: a1b2c3d4e5f6
Revises: cfb90e417b97
Create Date: 2026-07-09 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'cfb90e417b97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('students', sa.Column('class_name', sa.String(length=160), nullable=True))
    op.create_index(op.f('ix_students_class_name'), 'students', ['class_name'])
    op.add_column('schedules', sa.Column('class_name', sa.String(length=160), nullable=True))


def downgrade() -> None:
    op.drop_column('schedules', 'class_name')
    op.drop_index(op.f('ix_students_class_name'), table_name='students')
    op.drop_column('students', 'class_name')
