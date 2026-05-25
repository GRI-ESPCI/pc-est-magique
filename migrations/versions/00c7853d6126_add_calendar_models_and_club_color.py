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
        op.execute("ALTER TYPE permission_scope ADD VALUE IF NOT EXISTS 'club'")
        op.execute("ALTER TYPE permission_scope ADD VALUE IF NOT EXISTS 'calendar'")

    # --- INSERT DEFAULT CLUBS ---
    op.execute("INSERT INTO club (name, color) VALUES ('Club Q', '#dc8add') ON CONFLICT (name) DO NOTHING")
    op.execute("INSERT INTO club (name, color) VALUES ('Autre', '#757575') ON CONFLICT (name) DO NOTHING")

    # --- INSERT CALENDAR PERMISSIONS & ASSIGN TO ROLES ---
    op.execute(
        "INSERT INTO permission (type, scope, ref_id) "
        "SELECT 'read'::permission_type, 'calendar'::permission_scope, NULL "
        "WHERE NOT EXISTS ( "
        "    SELECT 1 FROM permission WHERE type = 'read' AND scope = 'calendar' AND ref_id IS NULL "
        ")"
    )
    op.execute(
        "INSERT INTO permission (type, scope, ref_id) "
        "SELECT 'all'::permission_type, 'calendar'::permission_scope, NULL "
        "WHERE NOT EXISTS ( "
        "    SELECT 1 FROM permission WHERE type = 'all' AND scope = 'calendar' AND ref_id IS NULL "
        ")"
    )
    op.execute(
        "INSERT INTO _role_permission_at (_role_id, _permission_id) "
        "SELECT r.id, p.id "
        "FROM role r, permission p "
        "WHERE r.name = 'Admin' AND p.type = 'all' AND p.scope = 'calendar' AND p.ref_id IS NULL "
        "ON CONFLICT DO NOTHING"
    )
    op.execute(
        "INSERT INTO _role_permission_at (_role_id, _permission_id) "
        "SELECT r.id, p.id "
        "FROM role r, permission p "
        "WHERE r.name = 'Élève' AND p.type = 'read' AND p.scope = 'calendar' AND p.ref_id IS NULL "
        "ON CONFLICT DO NOTHING"
    )


def downgrade():
    op.drop_table('event')
    op.drop_table('club')
    # Note: Cannot easily remove values from ENUM in PostgreSQL.
    pass
