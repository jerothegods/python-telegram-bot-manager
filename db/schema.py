import sqlalchemy as sa
from db.enums import *

meta = sa.MetaData()

user = sa.Table(
    'user',
    meta,
    sa.Column('user_id', sa.Integer, nullable=False, primary_key=True),
    sa.Column('is_bot', sa.Boolean, nullable=False),
    sa.Column('first_name', sa.String, nullable=False),
    sa.Column('last_name', sa.String, nullable=True),
    sa.Column('username', sa.String, nullable=True, unique=True),
    sa.Column('language_code', sa.String, nullable=False),
)

chat_photo = sa.Table(
    'chat_photo',
    meta,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('small_file_id', sa.String, nullable=False),
    sa.Column('big_file_id', sa.String, nullable=False),
)

chat = sa.Table(
    'chat',
    meta,
    sa.Column('chat_id', sa.BigInteger, primary_key=True),
    sa.Column('type', sa.Enum(CHAT_TYPES), nullable=False),
    sa.Column('title', sa.String, nullable=False),
    sa.Column('username', sa.String, nullable=True),
    sa.Column('first_name', sa.String, nullable=False),
    sa.Column('last_name', sa.String, nullable=True),
    sa.Column('all_members_are_administrators', sa.Boolean, nullable=False),
    sa.Column('photo', sa.ForeignKey('chat_photo.id'), nullable=True),
    sa.Column('description', sa.String, nullable=True),
    sa.Column('invite_link', sa.String, nullable=True),
    sa.Column('pinned', sa.Boolean, nullable=False),
    sa.Column('sticker_set_name', sa.String, nullable=True),
    sa.Column('can_set_sticker_set', sa.Boolean, nullable=False),
)

# photo_size = sa.Table(
#     'photo_size',
#     meta,
#     sa.Column('file_id', sa.String, primary_key=True),
#     sa.Column('width', sa.Integer, nullable=False),
#     sa.Column('height', sa.Integer, nullable=False),
#     sa.Column('file_size', sa.Integer, nullable=False),
# )

contact = sa.Table(
    'contact',
    meta,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('phone_number', sa.String, nullable=False),
    sa.Column('first_name', sa.String, nullable=False),
    sa.Column('last_name', sa.String, nullable=True),
    sa.Column('user_id', sa.Integer, nullable=True),
    sa.Column('vcard', sa.String, nullable=True)
)

location = sa.Table(
    'location',
    meta,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('latitude', sa.DECIMAL(10, 8)),
    sa.Column('longitude', sa.DECIMAL(11, 8)),
)

message = sa.Table(
    'message',
    meta,
    sa.Column('message_id', sa.Integer, primary_key=True),
    sa.Column('from_user', sa.ForeignKey('user.user_id'), nullable=False),
    sa.Column('date', sa.DateTime, nullable=False),
    sa.Column('chat', sa.ForeignKey('chat.chat_id'), nullable=False),
    sa.Column('forward_from', sa.ForeignKey('user.user_id'), nullable=True),
    sa.Column('forward_from_chat', sa.ForeignKey('chat.chat_id'), nullable=True),
    sa.Column('forward_from_message_id', sa.ForeignKey('message.message_id'), nullable=True),
    sa.Column('forward_date', sa.DateTime, nullable=True),
    sa.Column('reply_to_message', sa.ForeignKey('message.message_id'), nullable=True),
    sa.Column('edit_date', sa.DateTime, nullable=True),
    sa.Column('text', sa.String, nullable=True),
    # audio
    # document
    # animation
    # game
    # photo
    # sticker
    # video
    # voice
    # video_note
    # new_chat_members
    sa.Column('caption', sa.String, nullable=True),
    sa.Column('contact', sa.ForeignKey('contact.id'), nullable=True),
    sa.Column('location', sa.ForeignKey('location.id'), unique=True, nullable=True),
    # venue
    # left_chat_member
    # new_chat_title
    # new_chat_photo
    # delete_chat_photo
    # group_chat_created
    # supergroup_chat_created
    # channel_chat_created
    # migrate_to_chat_id
    # migrate_from_chat_id
    # pinned_message
    # invoice
    # successful_payment
    # connected_website
    # forward_signature
    # passport_data
    sa.Column('deleted', sa.Boolean, nullable=False),
)