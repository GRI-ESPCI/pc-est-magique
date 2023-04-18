"""empty message

Revision ID: ec764f0f21a4
Revises: 410c2b098e9e
Create Date: 2023-03-20 16:54:23.558949

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ec764f0f21a4'
down_revision = '410c2b098e9e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('club_q_client',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('mecontentement', sa.Float(), nullable=False),
    sa.Column('mecontentement_precedent', sa.Float(), nullable=False),
    sa.Column('saison_actuelle_mec', sa.Integer(), nullable=False),
    sa.Column('a_payer', sa.Float(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('club_q_salle',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nom', sa.String(length=64), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.Column('url', sa.String(length=64), nullable=True),
    sa.Column('adresse', sa.String(length=64), nullable=True),
    sa.Column('latitude', sa.Float(), nullable=True),
    sa.Column('longitude', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('club_q_season',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nom', sa.String(length=64), nullable=False),
    sa.Column('promo_orga', sa.Integer(), nullable=False),
    sa.Column('debut', sa.DateTime(), nullable=True),
    sa.Column('fin', sa.DateTime(), nullable=True),
    sa.Column('fin_inscription', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('club_q_spectacle',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nom', sa.String(length=64), nullable=False),
    sa.Column('categorie', sa.String(length=64), nullable=True),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('nb_tickets', sa.Integer(), nullable=False),
    sa.Column('unit_price', sa.Float(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('club_q_voeux',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('places_demandees', sa.Integer(), nullable=False),
    sa.Column('priorite', sa.Integer(), nullable=False),
    sa.Column('places_minimum', sa.Integer(), nullable=True),
    sa.Column('places_attribuees', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('club_q_voeux')
    op.drop_table('club_q_spectacle')
    op.drop_table('club_q_season')
    op.drop_table('club_q_salle')
    op.drop_table('club_q_client')
    # ### end Alembic commands ###
