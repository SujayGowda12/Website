"""Add file_path column to Risk table

Revision ID: ff37783bf3cc
Revises: 
Create Date: 2025-03-01 15:27:48.508303

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ff37783bf3cc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('risk', schema=None) as batch_op:
        batch_op.add_column(sa.Column('file_path', sa.String(length=200), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('risk', schema=None) as batch_op:
        batch_op.drop_column('file_path')

    # ### end Alembic commands ###
