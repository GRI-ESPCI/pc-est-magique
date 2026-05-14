"""add calendar models and club color

Revision ID: 00c7853d6126
Revises: 4e0058cdde5a
Create Date: 2026-05-14 07:02:18.079486

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '00c7853d6126'
down_revision = '4e0058cdde5a'
branch_labels = None
depends_on = None


def upgrade():
    # --- CREATION OF TABLES ---
    op.create_table('club',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('color', sa.String(length=7), nullable=False, server_default="#000000"),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_table('event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=128), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('all_day', sa.Boolean(), nullable=False),
        sa.Column('_author_id', sa.Integer(), nullable=False),
        sa.Column('_club_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['_author_id'], ['pceen.id'], ),
        sa.ForeignKeyConstraint(['_club_id'], ['club.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # --- UPDATE PERMISSION ENUM ---
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE permission_scope ADD VALUE 'club'")
        op.execute("ALTER TYPE permission_scope ADD VALUE 'calendar'")

    # --- INSERT DEFAULT CLUBS ---
    op.execute("INSERT INTO club (name, color) VALUES ('Club Q', '#dc8add') ON CONFLICT (name) DO NOTHING")
    op.execute("INSERT INTO club (name, color) VALUES ('Autre', '#757575') ON CONFLICT (name) DO NOTHING")


def downgrade():
    op.drop_table('event')
    op.drop_table('club')
    # Note: Cannot easily remove values from ENUM in PostgreSQL.
    pass
