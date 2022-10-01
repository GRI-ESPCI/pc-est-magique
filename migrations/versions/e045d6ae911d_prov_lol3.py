"""prov lol3

Revision ID: e045d6ae911d
Revises: cd158493c08f
Create Date: 2022-10-01 19:20:23.503488

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e045d6ae911d"
down_revision = "cd158493c08f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("bar_item", sa.Column("archived", sa.Boolean(), nullable=False))


def downgrade():
    op.drop_column("bar_item", "archived")
