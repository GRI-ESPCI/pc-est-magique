"""prov lol2

Revision ID: cd158493c08f
Revises: f83e2a07cdb1
Create Date: 2022-10-01 16:46:22.647425

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "cd158493c08f"
down_revision = "f83e2a07cdb1"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION unaccent;")
    pass


def downgrade():
    op.execute("DROP EXTENSION unaccent;")
    pass
