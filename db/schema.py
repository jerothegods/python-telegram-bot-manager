import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sapg
import uuid

meta = sa.MetaData()

user = sa.Table(
    'custom_job',
    meta,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('user_id', sa.Integer, nullable=False),
    sa.Column('is_bot', sa.Boolean, nullable=False),
    sa.Column('first_name', sa.String, nullable=False),
    sa.Column('last_name', sa.String, nullable=False),
    sa.Column('username', sa.String, nullable=False),
    # sa.Column('language_code', sa.String, nullable=False),
)