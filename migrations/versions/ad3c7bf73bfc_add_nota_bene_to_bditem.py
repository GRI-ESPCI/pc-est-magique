"""add_nota_bene_to_bditem

Revision ID: ad3c7bf73bfc
Revises: 9328d06d4d01
Create Date: 2026-10-16 21:35:06.389273

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ad3c7bf73bfc'
down_revision = '9328d06d4d01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('bd_item', schema=None) as batch_op:
        batch_op.add_column(sa.Column('nota_bene', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('bd_item', schema=None) as batch_op:
        batch_op.drop_column('nota_bene')
