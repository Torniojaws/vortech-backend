"""Added ReleaseCode to Releases model

Revision ID: c4567eb07fd9
Revises: a5e8f6d68ca7
Create Date: 2017-11-02 20:56:49.713362

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4567eb07fd9'
down_revision = 'a5e8f6d68ca7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Releases', sa.Column('ReleaseCode', sa.String(length=10), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Releases', 'ReleaseCode')
    # ### end Alembic commands ###