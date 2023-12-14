"""V4A full_description

Revision ID: 2321510adecf
Revises: 14a7cb835d43
Create Date: 2023-12-14 00:25:31.905938

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2321510adecf'
down_revision = '14a7cb835d43'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('v4a', sa.Column('full_description', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('v4a', 'full_description')
    # ### end Alembic commands ###