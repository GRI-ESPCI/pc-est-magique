"""empty message

Revision ID: 410c2b098e9e
Revises: c40acbec57fe
Create Date: 2023-01-29 19:40:22.427990

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '410c2b098e9e'
down_revision = 'c40acbec57fe'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('representation', sa.Column('_spectacle_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'representation', 'spectacle', ['_spectacle_id'], ['id'])
    op.alter_column('spectacle', 'image_name',
               existing_type=sa.VARCHAR(length=120),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('spectacle', 'image_name',
               existing_type=sa.VARCHAR(length=120),
               nullable=False)
    op.drop_constraint(None, 'representation', type_='foreignkey')
    op.drop_column('representation', '_spectacle_id')
    # ### end Alembic commands ###
