"""empty message

Revision ID: 41de1793dc42
Revises: 
Create Date: 2022-06-28 16:37:39.221317

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '41de1793dc42'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Dashboard')
    op.drop_table('Posts')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Posts',
    sa.Column('id', sa.INTEGER(), server_default=sa.text('nextval(\'"Posts_id_seq"\'::regclass)'), autoincrement=True, nullable=False),
    sa.Column('post_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('post_date', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('post_text', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('post_comments', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('post_likes', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('post_reposts', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('post_views', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('post_origin', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('post_author', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('post_img', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='Posts_pkey')
    )
    op.create_table('Dashboard',
    sa.Column('id', sa.INTEGER(), server_default=sa.text('nextval(\'"Dashboard_id_seq"\'::regclass)'), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('block_name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('block_order', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('block_options', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('block_data', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='Dashboard_pkey')
    )
    # ### end Alembic commands ###
