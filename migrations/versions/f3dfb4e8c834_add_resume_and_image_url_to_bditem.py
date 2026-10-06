"""add resume and image_url to BDItem

Revision ID: f3dfb4e8c834
Revises: 6e49e825be5e
Create Date: 2026-10-06 23:41:15.509343

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f3dfb4e8c834'
down_revision = '6e49e825be5e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('bd_item', schema=None) as batch_op:
        batch_op.add_column(sa.Column('resume', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('image_url', sa.String(length=500), nullable=True))

def downgrade():
    with op.batch_alter_table('bd_item', schema=None) as batch_op:
        batch_op.drop_column('image_url')
        batch_op.drop_column('resume')
