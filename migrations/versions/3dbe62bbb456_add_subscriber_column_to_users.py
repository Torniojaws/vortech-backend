"""Add subscriber column to users

Revision ID: 3dbe62bbb456
Revises: b3e0d6e8b6a3
Create Date: 2018-04-09 12:58:42.620691

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3dbe62bbb456'
down_revision = 'b3e0d6e8b6a3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Users', sa.Column('Subscriber', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Users', 'Subscriber')
    # ### end Alembic commands ###
