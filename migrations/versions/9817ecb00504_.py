"""empty message

Revision ID: 9817ecb00504
Revises: 5a1908859504
Create Date: 2023-03-21 20:28:52.887469

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9817ecb00504'
down_revision = '5a1908859504'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('club_q_client')
    op.drop_table('club_q_spectacle')
    op.drop_table('club_q_salle')
    op.drop_table('club_q_season')
    op.drop_table('club_q_voeux')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('club_q_voeux',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('places_demandees', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('priorite', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('places_minimum', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('places_attribuees', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('_client_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('_spectacle_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['_client_id'], ['club_q_client.id'], name='club_q_voeux__client_id_fkey'),
    sa.ForeignKeyConstraint(['_spectacle_id'], ['club_q_spectacle.id'], name='club_q_voeux__spectacle_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='club_q_voeux_pkey')
    )
    op.create_table('club_q_season',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('club_q_season_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('nom', sa.VARCHAR(length=64), autoincrement=False, nullable=False),
    sa.Column('promo_orga', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('debut', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('fin', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('fin_inscription', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='club_q_season_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('club_q_salle',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('club_q_salle_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('nom', sa.VARCHAR(length=64), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(length=500), autoincrement=False, nullable=True),
    sa.Column('url', sa.VARCHAR(length=64), autoincrement=False, nullable=True),
    sa.Column('adresse', sa.VARCHAR(length=64), autoincrement=False, nullable=True),
    sa.Column('latitude', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('lontitude', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='club_q_salle_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('club_q_spectacle',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('nom', sa.VARCHAR(length=64), autoincrement=False, nullable=False),
    sa.Column('categorie', sa.VARCHAR(length=64), autoincrement=False, nullable=True),
    sa.Column('description', sa.VARCHAR(length=500), autoincrement=False, nullable=True),
    sa.Column('date', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('nb_tickets', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('unit_price', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('_season_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('_salle_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['_salle_id'], ['club_q_salle.id'], name='club_q_spectacle__salle_id_fkey'),
    sa.ForeignKeyConstraint(['_season_id'], ['club_q_season.id'], name='club_q_spectacle__season_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='club_q_spectacle_pkey')
    )
    op.create_table('club_q_client',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('mecontentement', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('mecontentement_precedent', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('saison_actuelle_mec', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('a_payer', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='club_q_client_pkey')
    )
    # ### end Alembic commands ###
