"""add_club_q_payment_and_salle_respo

Revision ID: c8d3e9f1a012
Revises: e5f7a9c1b2d3
Create Date: 2026-11-21 09:48:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8d3e9f1a012'
down_revision = 'e5f7a9c1b2d3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'club_q_payment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paid', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('_pceen_id', sa.Integer(), nullable=False),
        sa.Column('_season_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['_pceen_id'], ['pceen.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['_season_id'], ['club_q_season.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('_pceen_id', '_season_id', name='uq_club_q_payment_pceen_season'),
    )
    op.create_index('ix_club_q_payment_season_id', 'club_q_payment', ['_season_id'])

    op.create_table(
        'club_q_salle_respo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('_salle_id', sa.Integer(), nullable=False),
        sa.Column('_season_id', sa.Integer(), nullable=False),
        sa.Column('_pceen_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['_salle_id'], ['club_q_salle.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['_season_id'], ['club_q_season.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['_pceen_id'], ['pceen.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('_salle_id', '_season_id', name='uq_club_q_salle_respo_salle_season'),
    )
    op.create_index('ix_club_q_salle_respo_pceen_season', 'club_q_salle_respo', ['_pceen_id', '_season_id'])
    op.create_index('ix_club_q_salle_respo_season_id', 'club_q_salle_respo', ['_season_id'])

    op.execute(
        """
        DELETE FROM club_q_voeu v
        USING club_q_voeu newer
        WHERE v._pceen_id = newer._pceen_id
          AND v._spectacle_id = newer._spectacle_id
          AND v.id < newer.id
        """
    )
    op.create_unique_constraint(
        'uq_club_q_voeu_pceen_spectacle', 'club_q_voeu', ['_pceen_id', '_spectacle_id']
    )


def downgrade():
    op.drop_constraint('uq_club_q_voeu_pceen_spectacle', 'club_q_voeu', type_='unique')

    op.drop_index('ix_club_q_salle_respo_season_id', table_name='club_q_salle_respo')
    op.drop_index('ix_club_q_salle_respo_pceen_season', table_name='club_q_salle_respo')
    op.drop_table('club_q_salle_respo')

    op.drop_index('ix_club_q_payment_season_id', table_name='club_q_payment')
    op.drop_table('club_q_payment')
