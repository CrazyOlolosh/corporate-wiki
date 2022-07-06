"""empty message

Revision ID: 4a51d25dd641
Revises: 721d8221377e
Create Date: 2022-07-04 17:32:49.395957

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a51d25dd641'
down_revision = '721d8221377e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Spaces')
    op.drop_table('Versions')
    op.drop_table('Pages')
    op.drop_table('Comments')
    op.drop_table('user')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('user_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('username', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
    sa.Column('email', sa.VARCHAR(length=120), autoincrement=False, nullable=False),
    sa.Column('pwd', sa.VARCHAR(length=300), autoincrement=False, nullable=False),
    sa.Column('role', sa.VARCHAR(length=30), autoincrement=False, nullable=True),
    sa.Column('user_pic', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('confirmed', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('fav_spaces', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('allowed_spaces', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('fav_pages', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('allowed_pages', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='user_pkey'),
    sa.UniqueConstraint('email', name='user_email_key'),
    sa.UniqueConstraint('pwd', name='user_pwd_key'),
    sa.UniqueConstraint('username', name='user_username_key'),
    postgresql_ignore_search_path=False
    )
    op.create_table('Comments',
    sa.Column('id', sa.INTEGER(), server_default=sa.text('nextval(\'"Comments_id_seq"\'::regclass)'), autoincrement=True, nullable=False),
    sa.Column('page_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('author', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('text', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('time', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['author'], ['user.id'], name='Comments_author_fkey'),
    sa.ForeignKeyConstraint(['page_id'], ['Pages.id'], name='Comments_page_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='Comments_pkey')
    )
    op.create_table('Pages',
    sa.Column('id', sa.INTEGER(), server_default=sa.text('nextval(\'"Pages_id_seq"\'::regclass)'), autoincrement=True, nullable=False),
    sa.Column('title', sa.VARCHAR(length=120), autoincrement=False, nullable=False),
    sa.Column('author', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
    sa.Column('text', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('limitations', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('date', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('parent', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('space', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['parent'], ['Pages.id'], name='children'),
    sa.PrimaryKeyConstraint('id', name='Pages_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('Versions',
    sa.Column('id', sa.INTEGER(), server_default=sa.text('nextval(\'"Versions_id_seq"\'::regclass)'), autoincrement=True, nullable=False),
    sa.Column('page_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('version', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('title', sa.VARCHAR(length=120), autoincrement=False, nullable=False),
    sa.Column('text', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('author', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('time', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['author'], ['user.username'], name='Versions_author_fkey'),
    sa.ForeignKeyConstraint(['page_id'], ['Pages.id'], name='Versions_page_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='Versions_pkey')
    )
    op.create_table('Spaces',
    sa.Column('id', sa.INTEGER(), server_default=sa.text('nextval(\'"Spaces_id_seq"\'::regclass)'), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('members', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('limitations', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('logo', sa.VARCHAR(), server_default=sa.text("''::character varying"), autoincrement=False, nullable=True),
    sa.Column('homepage', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('parent', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='Spaces_pkey')
    )
    # ### end Alembic commands ###
