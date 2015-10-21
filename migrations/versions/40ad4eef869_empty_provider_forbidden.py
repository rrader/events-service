"""empty provider forbidden

Revision ID: 40ad4eef869
Revises: 33753269335
Create Date: 2015-10-21 12:33:10.692233

"""

# revision identifiers, used by Alembic.
revision = '40ad4eef869'
down_revision = '33753269335'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('events', 'provider',
               existing_type=sa.INTEGER(),
               nullable=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('events', 'provider',
               existing_type=sa.INTEGER(),
               nullable=True)
    ### end Alembic commands ###
