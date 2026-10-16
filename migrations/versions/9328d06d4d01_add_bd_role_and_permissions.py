"""add_bd_role_and_permissions

Revision ID: 9328d06d4d01
Revises: f3dfb4e8c834
Create Date: 2026-10-16 20:47:45.420311

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9328d06d4d01'
down_revision = 'f3dfb4e8c834'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        INSERT INTO permission (type, scope)
        SELECT 'all', 'bd'
        WHERE NOT EXISTS (
            SELECT 1 FROM permission
            WHERE type = 'all' AND scope = 'bd' AND ref_id IS NULL
        )
    """)

    op.execute("""
        INSERT INTO role (name, index, color)
        SELECT 'BD', 19, '3c78d8'
        WHERE NOT EXISTS (
            SELECT 1 FROM role WHERE name = 'BD'
        )
    """)

    op.execute("""
        INSERT INTO _role_permission_at (_role_id, _permission_id)
        SELECT role.id, permission.id
        FROM role, permission
        WHERE role.name = 'BD'
          AND permission.type = 'all'
          AND permission.scope = 'bd'
          AND permission.ref_id IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM _role_permission_at
              WHERE _role_id = role.id AND _permission_id = permission.id
          )
    """)


def downgrade():
    # Remove associations with BD role
    op.execute("""
        DELETE FROM _role_permission_at
        WHERE _role_id IN (SELECT id FROM role WHERE name = 'BD')
    """)

    # Remove BD role
    op.execute("DELETE FROM role WHERE name = 'BD'")

    # Remove associations for bd permission
    op.execute("""
        DELETE FROM _role_permission_at
        WHERE _permission_id IN (
            SELECT id FROM permission WHERE scope = 'bd'
        )
    """)

    # Remove permission for bd
    op.execute("DELETE FROM permission WHERE scope = 'bd'")
