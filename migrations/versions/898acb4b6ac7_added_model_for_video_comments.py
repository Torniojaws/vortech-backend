"""Added model for video comments

Revision ID: 898acb4b6ac7
Revises: c53ca3f4f74e
Create Date: 2018-03-31 01:03:02.334664

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '898acb4b6ac7'
down_revision = 'c53ca3f4f74e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('CommentsVideos',
    sa.Column('CommentID', sa.Integer(), nullable=False),
    sa.Column('VideoID', sa.Integer(), nullable=False),
    sa.Column('Comment', sa.Text(), nullable=False),
    sa.Column('UserID', sa.Integer(), nullable=False),
    sa.Column('Created', sa.DateTime(), nullable=True),
    sa.Column('Updated', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['UserID'], ['Users.UserID'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['VideoID'], ['Videos.VideoID'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('CommentID')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('CommentsVideos')
    # ### end Alembic commands ###
