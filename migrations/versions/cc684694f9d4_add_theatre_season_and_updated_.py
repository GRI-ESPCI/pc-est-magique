"""Add theatre season and updated Spectacle model for one_to_many relationship

Revision ID: cc684694f9d4
Revises: cd25f6f41bd7
Create Date: 2025-04-21 16:46:05.739464

"""
import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc684694f9d4'
down_revision = 'cd25f6f41bd7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    saison = op.create_table('saison',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('description', sa.String(length=2000), nullable=True),
    sa.Column('image_name', sa.String(length=120), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.bulk_insert(
        saison,
        [{"id": 0, "name": "Anciennes saisons", "start_date": datetime.date(2025, 3, 10)}]
    )
    op.add_column('spectacle', sa.Column('_saison_id', sa.Integer(), nullable=False, server_default="0"))
    op.create_foreign_key(None, 'spectacle', 'saison', ['_saison_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'spectacle', type_='foreignkey')
    op.drop_column('spectacle', '_saison_id')
    op.drop_table('saison')
    # ### end Alembic commands ###
