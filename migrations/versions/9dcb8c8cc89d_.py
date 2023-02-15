"""empty message

Revision ID: 9dcb8c8cc89d
Revises: 76aaff18d81b
Create Date: 2023-01-29 19:16:11.772769

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9dcb8c8cc89d'
down_revision = '76aaff18d81b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('theatre_representation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('theatre_spectacle',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('description', sa.String(length=2000), nullable=True),
    sa.Column('ticket_link', sa.String(length=120), nullable=True),
    sa.Column('director', sa.String(length=64), nullable=True),
    sa.Column('author', sa.String(length=64), nullable=True),
    sa.Column('image_name', sa.String(length=120), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('theatre_spectacle')
    op.drop_table('theatre_representation')
    # ### end Alembic commands ###