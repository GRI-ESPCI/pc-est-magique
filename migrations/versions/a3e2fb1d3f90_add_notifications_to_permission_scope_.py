"""add notifications to permission_scope enum

Revision ID: a3e2fb1d3f90
Revises: 387781c82e8e
Create Date: 2026-08-30 21:19:20.883891

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3e2fb1d3f90'
down_revision = '387781c82e8e'
branch_labels = None
depends_on = None


def upgrade():
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE permission_scope ADD VALUE IF NOT EXISTS 'notifications'")

def downgrade():
    pass
