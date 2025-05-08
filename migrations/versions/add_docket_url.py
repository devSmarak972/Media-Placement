"""Add docket_url column to MediaPlacement model

Revision ID: add_docket_url
Revises: 
Create Date: 2025-05-07 21:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_docket_url'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('media_placements', sa.Column('docket_url', sa.String(length=512), nullable=True))


def downgrade():
    op.drop_column('media_placements', 'docket_url')