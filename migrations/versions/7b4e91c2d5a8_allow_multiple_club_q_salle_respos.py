"""allow_multiple_club_q_salle_respos

Revision ID: 7b4e91c2d5a8
Revises: c8d3e9f1a012
Create Date: 2026-11-26 19:12:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b4e91c2d5a8'
down_revision = 'c8d3e9f1a012'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('uq_club_q_salle_respo_salle_season', 'club_q_salle_respo', type_='unique')
    op.create_unique_constraint(
        'uq_club_q_salle_respo_salle_season_pceen',
        'club_q_salle_respo',
        ['_salle_id', '_season_id', '_pceen_id'],
    )


def downgrade():
    op.drop_constraint('uq_club_q_salle_respo_salle_season_pceen', 'club_q_salle_respo', type_='unique')
    op.execute(
        """
        DELETE FROM club_q_salle_respo r
        USING club_q_salle_respo newer
        WHERE r._salle_id = newer._salle_id
          AND r._season_id = newer._season_id
          AND r.id < newer.id
        """
    )
    op.create_unique_constraint(
        'uq_club_q_salle_respo_salle_season',
        'club_q_salle_respo',
        ['_salle_id', '_season_id'],
    )
