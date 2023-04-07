"""empty message

Revision ID: 8af1d33aa52f
Revises: c378668b1992
Create Date: 2023-04-02 20:38:22.143931

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8af1d33aa52f'
down_revision = 'c378668b1992'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('club_q_voeux',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('places_demandees', sa.Integer(), nullable=False),
    sa.Column('priorite', sa.Integer(), nullable=False),
    sa.Column('places_minimum', sa.Integer(), nullable=True),
    sa.Column('places_attribuees', sa.Integer(), nullable=True),
    sa.Column('_client_id', sa.Integer(), nullable=False),
    sa.Column('_spectacle_id', sa.Integer(), nullable=False),
    sa.Column('_season_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['_client_id'], ['pceen.id'], ),
    sa.ForeignKeyConstraint(['_season_id'], ['club_q_season.id'], ),
    sa.ForeignKeyConstraint(['_spectacle_id'], ['club_q_spectacle.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('club_q_voeux')
    # ### end Alembic commands ###
