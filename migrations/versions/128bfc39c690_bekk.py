"""bekk

Revision ID: 128bfc39c690
Revises: 4f578e0fb6a0
Create Date: 2023-09-18 21:07:01.563912

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '128bfc39c690'
down_revision = '4f578e0fb6a0'
branch_labels = None
depends_on = None

old_options = (
    "photos",
    "pceen",
    "collection",
    "album",
    "role",
    "bar",
    "bar_stats",
    "intrarez",
    "club_q",
)
new_options = sorted(old_options + ("bekk",))

old_type = sa.Enum(*old_options, name="permission_scope")
new_type = sa.Enum(*new_options, name="permission_scope")
tmp_type = sa.Enum(*new_options, name="_permission_scope")


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('bekk',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('promo', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.alter_column('club_q_salle', 'latitude',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=False,
               existing_server_default=sa.text('0'))
    op.alter_column('club_q_salle', 'longitude',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=False,
               existing_server_default=sa.text('0'))
    

    # Create a temporary "_permission_scope" type, convert and drop the "old" type
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE permission ALTER COLUMN scope TYPE _permission_scope USING scope::text::_permission_scope")
    old_type.drop(op.get_bind(), checkfirst=False)
    # Create and convert to the "new" scope type
    new_type.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE permission ALTER COLUMN scope TYPE permission_scope USING scope::text::permission_scope")
    tmp_type.drop(op.get_bind(), checkfirst=False)
    # ### end Alembic commands ###

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('club_q_salle', 'longitude',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=True,
               existing_server_default=sa.text('0'))
    op.alter_column('club_q_salle', 'latitude',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=True,
               existing_server_default=sa.text('0'))
    op.drop_table('bekk')

    # Convert 'output_limit_exceeded' scope into 'timed_out'
    op.execute("DELETE FROM permission WHERE scope='intrarez'")
    # Create a temporary "_permission_scope" type, convert and drop the "new" type
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE permission ALTER COLUMN scope TYPE _permission_scope USING scope::text::_permission_scope")
    new_type.drop(op.get_bind(), checkfirst=False)
    # Create and convert to the "old" scope type
    old_type.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE permission ALTER COLUMN scope TYPE permission_scope USING scope::text::permission_scope")
    tmp_type.drop(op.get_bind(), checkfirst=False)
    # ### end Alembic commands ###
