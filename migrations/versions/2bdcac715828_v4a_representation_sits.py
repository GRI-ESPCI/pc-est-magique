"""V4A representation sits

Revision ID: 2bdcac715828
Revises: 2321510adecf
Create Date: 2023-12-14 00:36:17.747753

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2bdcac715828'
down_revision = '2321510adecf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('v4a_representation', sa.Column('sits', sa.Integer(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('v4a_representation', 'sits')
    # ### end Alembic commands ###
