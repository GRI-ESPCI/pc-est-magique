"""fix_pceen_discontent_numeric_precision

Revision ID: c4e91a8b204f
Revises: 8a4f9c12e301
Create Date: 2026-11-02 23:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4e91a8b204f'
down_revision = '8a4f9c12e301'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('pceen', schema=None) as batch_op:
        batch_op.alter_column(
            'discontent',
            existing_type=sa.Numeric(precision=2, asdecimal=False),
            type_=sa.Numeric(precision=6, scale=2, asdecimal=False),
            existing_nullable=True,
        )


def downgrade():
    with op.batch_alter_table('pceen', schema=None) as batch_op:
        batch_op.alter_column(
            'discontent',
            existing_type=sa.Numeric(precision=6, scale=2, asdecimal=False),
            type_=sa.Numeric(precision=2, asdecimal=False),
            existing_nullable=True,
        )
