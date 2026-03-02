"""Add unaccent extension

Revision ID: 170f7a7dced9
Revises: fa3a7ab1bc06
Create Date: 2026-03-02 21:34:48.531423

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '170f7a7dced9'
down_revision = 'fa3a7ab1bc06'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
    op.add_column("pceen", sa.Column("espci_email", sa.String(length=120), nullable=True))


def downgrade():
    op.drop_column("pceen", "espci_email")
    op.execute("DROP EXTENSION IF EXISTS unaccent;")
