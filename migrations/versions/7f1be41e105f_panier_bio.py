"""panier-bio

Revision ID: 7f1be41e105f
Revises: 01a8183de4df
Create Date: 2023-11-11 23:09:56.591635

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7f1be41e105f"
down_revision = "01a8183de4df"
branch_labels = None
depends_on = None

old_options = ("photos", "pceen", "collection", "album", "role", "bar", "bar_stats", "intrarez", "club_q", "bekk")
new_options = sorted(old_options + ("panier_bio", "theatre"))

old_type = sa.Enum(*old_options, name="permission_scope")
new_type = sa.Enum(*new_options, name="permission_scope")
tmp_type = sa.Enum(*new_options, name="_permission_scope")


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("spectacle", sa.Column("year", sa.Integer(), nullable=True))
    op.execute("UPDATE spectacle SET year = 2024::int;")
    op.alter_column("spectacle", "year", nullable=True)

    op.create_table(
        "order_panier_bio",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("service", sa.String(length=50), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("payment_method", sa.String(length=120), nullable=False),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column("phone_number", sa.String(length=20), nullable=True),
        sa.Column("payment_made", sa.Boolean(), nullable=False),
        sa.Column("treasurer_validate", sa.Boolean(), nullable=False),
        sa.Column("taken", sa.Boolean(), nullable=False),
        sa.Column("_period_id", sa.Integer(), nullable=False),
        sa.Column("_pceen_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["_pceen_id"],
            ["pceen.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "period_panier_bio",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("disabled_days", sa.String(length=500), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_foreign_key(None, "order_panier_bio", "period_panier_bio", ["_period_id"], ["id"])
    # ### end Alembic commands ###


"""
    # Create a temporary "_permission_scope" type, convert and drop the "old" type
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE permission ALTER COLUMN scope TYPE _permission_scope USING scope::text::_permission_scope")
    old_type.drop(op.get_bind(), checkfirst=False)
    # Create and convert to the "new" scope type
    new_type.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE permission ALTER COLUMN scope TYPE permission_scope USING scope::text::permission_scope")
    tmp_type.drop(op.get_bind(), checkfirst=False)
"""


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("order_panier_bio")
    op.drop_column("spectacle", "year")
    op.drop_table("period_panier_bio")
    # ### end Alembic commands ###

    # Create a temporary "_permission_scope" type, convert and drop the "new" type
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE permission ALTER COLUMN scope TYPE _permission_scope USING scope::text::_permission_scope")
    new_type.drop(op.get_bind(), checkfirst=False)
    # Create and convert to the "old" scope type
    old_type.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE permission ALTER COLUMN scope TYPE permission_scope USING scope::text::permission_scope")
    tmp_type.drop(op.get_bind(), checkfirst=False)