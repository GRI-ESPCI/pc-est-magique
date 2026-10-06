"""Add BD module (BDItem table)

Revision ID: 6e49e825be5e
Revises: a3e2fb1d3f90
Create Date: 2026-10-06 21:06:52.809823

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6e49e825be5e'
down_revision = 'a3e2fb1d3f90'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('bd_item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('auteurs', sa.String(length=500), nullable=False),
    sa.Column('titre', sa.String(length=500), nullable=False),
    sa.Column('date_publication', sa.String(length=50), nullable=True),
    sa.Column('editeur', sa.String(length=200), nullable=True),
    sa.Column('pages', sa.Integer(), nullable=True),
    sa.Column('isbn', sa.String(length=20), nullable=True),
    sa.Column('categorie', sa.String(length=20), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('bd_item', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_bd_item_isbn'), ['isbn'], unique=False)
        
    # Postgres ENUM update workaround
    op.execute("ALTER TYPE permission_scope ADD VALUE IF NOT EXISTS 'bd'")


def downgrade():
    with op.batch_alter_table('bd_item', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_bd_item_isbn'))
    op.drop_table('bd_item')
    # Note: postgres doesn't easily allow dropping an enum value
