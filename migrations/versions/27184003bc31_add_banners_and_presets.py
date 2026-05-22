"""add banners and presets

Revision ID: 27184003bc31
Revises: 00c7853d6126
Create Date: 2026-05-21 00:10:56.043249

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '27184003bc31'
down_revision = '00c7853d6126'
branch_labels = None
depends_on = None


def upgrade():
    # Create info_banner_preset
    op.create_table('info_banner_preset',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('background_color', sa.String(length=7), nullable=False),
        sa.Column('text_color', sa.String(length=7), nullable=False),
        sa.Column('icon', sa.String(length=64), nullable=True),
        sa.Column('image_filename', sa.String(length=128), nullable=True),
        sa.Column('text_alignment', sa.String(length=16), nullable=False, server_default='center'),
        sa.Column('layout_style', sa.String(length=16), nullable=False, server_default='vertical'),
        sa.Column('overlay_opacity', sa.Integer(), nullable=False, server_default='70'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create info_banner
    op.create_table('info_banner',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('is_text', sa.Boolean(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('background_color', sa.String(length=7), nullable=False),
        sa.Column('text_color', sa.String(length=7), nullable=False),
        sa.Column('image_filename', sa.String(length=128), nullable=True),
        sa.Column('link_url', sa.String(length=512), nullable=True),
        sa.Column('file_filename', sa.String(length=128), nullable=True),
        sa.Column('file_original_name', sa.String(length=128), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('_preset_id', sa.Integer(), nullable=True),
        sa.Column('icon', sa.String(length=64), nullable=True),
        sa.Column('text_alignment', sa.String(length=16), nullable=False, server_default='center'),
        sa.Column('layout_style', sa.String(length=16), nullable=False, server_default='vertical'),
        sa.Column('overlay_opacity', sa.Integer(), nullable=False, server_default='70'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['_preset_id'], ['info_banner_preset.id'], ondelete='SET NULL')
    )

    # Global Settings
    global_setting = sa.table('global_setting',
        sa.column('name_fr', sa.String),
        sa.column('name_en', sa.String),
        sa.column('key', sa.String),
        sa.column('value', sa.Integer)
    )
    # Ensure serial sequence is synced
    op.execute("""
        SELECT setval(pg_get_serial_sequence('global_setting', 'id'), coalesce(max(id), 0) + 1, false) 
        FROM global_setting;
    """)
    op.bulk_insert(global_setting, [
        {'name_fr': "Rapport d'aspect carrousel (Largeur)", 'name_en': 'Carousel aspect ratio (Width)', 'key': 'CAROUSEL_ASPECT_RATIO_X', 'value': 21},
        {'name_fr': "Rapport d'aspect carrousel (Hauteur)", 'name_en': 'Carousel aspect ratio (Height)', 'key': 'CAROUSEL_ASPECT_RATIO_Y', 'value': 9},
    ])

    # Calendrier Role
    op.execute(
        "INSERT INTO role (name, index, color) "
        "SELECT 'Calendrier', 50, 'E65100' "
        "WHERE NOT EXISTS (SELECT 1 FROM role WHERE name = 'Calendrier')"
    )
    op.execute(
        "INSERT INTO permission (type, scope, ref_id) "
        "SELECT 'write'::permission_type, 'calendar'::permission_scope, NULL "
        "WHERE NOT EXISTS ( "
        "    SELECT 1 FROM permission WHERE type = 'write' AND scope = 'calendar' AND ref_id IS NULL "
        ")"
    )
    op.execute(
        "INSERT INTO _role_permission_at (_role_id, _permission_id) "
        "SELECT r.id, p.id "
        "FROM role r, permission p "
        "WHERE r.name = 'Calendrier' AND p.type = 'write' AND p.scope = 'calendar' AND p.ref_id IS NULL "
        "ON CONFLICT DO NOTHING"
    )
    op.execute(
        "INSERT INTO _role_permission_at (_role_id, _permission_id) "
        "SELECT r.id, p.id "
        "FROM role r, permission p "
        "WHERE r.name = 'Calendrier' AND p.type = 'read' AND p.scope = 'calendar' AND p.ref_id IS NULL "
        "ON CONFLICT DO NOTHING"
    )


def downgrade():
    op.execute(
        "DELETE FROM _role_permission_at WHERE _role_id IN (SELECT id FROM role WHERE name = 'Calendrier')"
    )
    op.execute("DELETE FROM role WHERE name = 'Calendrier'")
    op.execute("DELETE FROM global_setting WHERE key IN ('CAROUSEL_ASPECT_RATIO_X', 'CAROUSEL_ASPECT_RATIO_Y')")
    op.drop_table('info_banner')
    op.drop_table('info_banner_preset')
