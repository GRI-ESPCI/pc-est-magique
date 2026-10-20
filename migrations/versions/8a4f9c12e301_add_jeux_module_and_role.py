"""add_jeux_module_and_role

Revision ID: 8a4f9c12e301
Revises: ad3c7bf73bfc
Create Date: 2026-10-20 22:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a4f9c12e301'
down_revision = 'ad3c7bf73bfc'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'jeu_item',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nom', sa.String(length=500), nullable=False),
        sa.Column('categorie', sa.String(length=100), nullable=False),
        sa.Column('temps_de_jeu', sa.String(length=100), nullable=True),
        sa.Column('nb_joueurs', sa.String(length=100), nullable=True),
        sa.Column('popularite', sa.String(length=100), nullable=True),
        sa.Column('commentaires', sa.Text(), nullable=True),
        sa.Column('resume', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('image_filename', sa.String(length=255), nullable=True),
        sa.Column('nota_bene', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'jeu_reservation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('_jeu_id', sa.Integer(), nullable=False),
        sa.Column('_pceen_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('cancelled', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['_jeu_id'], ['jeu_item.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['_pceen_id'], ['pceen.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('jeu_reservation', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_jeu_reservation__jeu_id'), ['_jeu_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_jeu_reservation__pceen_id'), ['_pceen_id'], unique=False)

    with op.batch_alter_table('notification', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pceen_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_notification_pceen_id'), ['pceen_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_notification_pceen_id',
            'pceen',
            ['pceen_id'],
            ['id'],
            ondelete='CASCADE',
        )

    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE permission_scope ADD VALUE IF NOT EXISTS 'jeux'")

    op.execute("""
        INSERT INTO permission (type, scope)
        SELECT 'read', 'jeux'
        WHERE NOT EXISTS (
            SELECT 1 FROM permission
            WHERE type = 'read' AND scope = 'jeux' AND ref_id IS NULL
        )
    """)

    op.execute("""
        INSERT INTO permission (type, scope)
        SELECT 'all', 'jeux'
        WHERE NOT EXISTS (
            SELECT 1 FROM permission
            WHERE type = 'all' AND scope = 'jeux' AND ref_id IS NULL
        )
    """)

    op.execute("""
        INSERT INTO role (name, index, color)
        SELECT 'Jeux', 19, 'e67e22'
        WHERE NOT EXISTS (
            SELECT 1 FROM role WHERE name = 'Jeux'
        )
    """)

    op.execute("""
        INSERT INTO _role_permission_at (_role_id, _permission_id)
        SELECT role.id, permission.id
        FROM role, permission
        WHERE role.name IN ('Jeux', 'Admin')
          AND permission.type = 'all'
          AND permission.scope = 'jeux'
          AND permission.ref_id IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM _role_permission_at
              WHERE _role_id = role.id AND _permission_id = permission.id
          )
    """)

    op.execute("""
        INSERT INTO _role_permission_at (_role_id, _permission_id)
        SELECT role.id, permission.id
        FROM role, permission
        WHERE role.name = 'Élève'
          AND permission.type = 'read'
          AND permission.scope = 'jeux'
          AND permission.ref_id IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM _role_permission_at
              WHERE _role_id = role.id AND _permission_id = permission.id
          )
    """)


def downgrade():
    with op.batch_alter_table('notification', schema=None) as batch_op:
        batch_op.drop_constraint('fk_notification_pceen_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_notification_pceen_id'))
        batch_op.drop_column('pceen_id')

    with op.batch_alter_table('jeu_reservation', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_jeu_reservation__pceen_id'))
        batch_op.drop_index(batch_op.f('ix_jeu_reservation__jeu_id'))
    op.drop_table('jeu_reservation')

    op.execute("""
        DELETE FROM _role_permission_at
        WHERE _role_id IN (SELECT id FROM role WHERE name = 'Jeux')
    """)
    op.execute("DELETE FROM role WHERE name = 'Jeux'")
    op.execute("""
        DELETE FROM _role_permission_at
        WHERE _permission_id IN (
            SELECT id FROM permission WHERE scope = 'jeux'
        )
    """)
    op.execute("DELETE FROM permission WHERE scope = 'jeux'")
    op.drop_table('jeu_item')
