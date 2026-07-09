"""add teachers and teacher_attendance tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-09 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'teachers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('photo_path', sa.String(length=512), nullable=True),
        sa.Column('face_embedding', Vector(512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_teachers_full_name'), 'teachers', ['full_name'])

    op.create_table(
        'teacher_attendance',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('attendance_date', sa.Date(), nullable=False),
        sa.Column('is_present', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('source', sa.String(length=20), nullable=False, server_default='manual'),
        sa.Column('marked_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('teacher_id', 'attendance_date', name='uq_teacher_attendance_unique'),
    )
    op.create_index(op.f('ix_teacher_attendance_teacher_id'), 'teacher_attendance', ['teacher_id'])
    op.create_index(op.f('ix_teacher_attendance_attendance_date'), 'teacher_attendance', ['attendance_date'])


def downgrade() -> None:
    op.drop_table('teacher_attendance')
    op.drop_index(op.f('ix_teachers_full_name'), table_name='teachers')
    op.drop_table('teachers')
