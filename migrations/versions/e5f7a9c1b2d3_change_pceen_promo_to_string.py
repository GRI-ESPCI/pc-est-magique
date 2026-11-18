"""change_pceen_promo_to_string

Revision ID: e5f7a9c1b2d3
Revises: c4e91a8b204f
Create Date: 2026-11-18 22:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5f7a9c1b2d3'
down_revision = 'c4e91a8b204f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('pceen', schema=None) as batch_op:
        batch_op.alter_column(
            'promo',
            existing_type=sa.Integer(),
            type_=sa.String(length=16),
            existing_nullable=True,
            postgresql_using="CASE WHEN promo = 0 THEN NULL ELSE promo::varchar(16) END",
        )


def downgrade():
    with op.batch_alter_table('pceen', schema=None) as batch_op:
        batch_op.alter_column(
            'promo',
            existing_type=sa.String(length=16),
            type_=sa.Integer(),
            existing_nullable=True,
            postgresql_using="CASE WHEN promo ~ '^[0-9]+$' THEN promo::integer ELSE NULL END",
        )
