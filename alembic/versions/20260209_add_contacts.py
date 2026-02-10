"""add contacts tables and avatar column

Revision ID: 20260209_add_contacts
Revises: 
Create Date: 2026-02-09 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260209_add_contacts'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add avatar_url column to Users table
    with op.batch_alter_table('Users') as batch_op:
        batch_op.add_column(sa.Column('avatar_url', sa.String(500), nullable=True))

    # Create ContactSetting table
    op.create_table(
        'ContactSetting',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('Users.user_id'), nullable=False),
        sa.Column('contact_id', sa.BigInteger(), sa.ForeignKey('Users.user_id'), nullable=False),
        sa.Column('alias', sa.String(100), nullable=True),
        sa.Column('is_blocked', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_unique_constraint('uq_contact_setting', 'ContactSetting', ['user_id', 'contact_id'])


def downgrade():
    op.drop_constraint('uq_contact_setting', 'ContactSetting', type_='unique')
    op.drop_table('ContactSetting')
    with op.batch_alter_table('Users') as batch_op:
        batch_op.drop_column('avatar_url')
