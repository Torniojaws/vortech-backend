"""Added author column to lyrics

Revision ID: 8fa899742973
Revises: 0f8db88d6a30
Create Date: 2018-03-24 10:26:29.210106

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8fa899742973'
down_revision = '0f8db88d6a30'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('SongsLyrics', sa.Column('Author', sa.String(length=190), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('SongsLyrics', 'Author')
    # ### end Alembic commands ###
