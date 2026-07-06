"""add phone camera fields to cameras

Revision ID: 2b1c2f54ea78
Revises: 4949d8cb1491
Create Date: 2026-07-06 20:58:16.429545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2b1c2f54ea78'
down_revision: Union[str, None] = '4949d8cb1491'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adding an Enum column to an EXISTING table via ALTER TABLE does not
    # auto-create the Postgres type the way `create_table` does; create it
    # explicitly first (checkfirst avoids a clash if it somehow already exists).
    camera_source_type = sa.Enum('IP_CAMERA', 'PHONE', name='camerasourcetype')
    camera_source_type.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'cameras',
        sa.Column(
            'source_type',
            camera_source_type,
            nullable=False,
            server_default='IP_CAMERA',
        ),
    )
    op.add_column('cameras', sa.Column('webrtc_token', sa.String(length=64), nullable=True))
    op.create_unique_constraint('uq_cameras_webrtc_token', 'cameras', ['webrtc_token'])


def downgrade() -> None:
    op.drop_constraint('uq_cameras_webrtc_token', 'cameras', type_='unique')
    op.drop_column('cameras', 'webrtc_token')
    op.drop_column('cameras', 'source_type')
    op.execute("DROP TYPE IF EXISTS camerasourcetype")
