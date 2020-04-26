from django.db import models
import django_telegram.constants as constants
import telegram.ext
from django.db.models.signals import post_init, pre_save
import json
import os
import Butlers
from django_telegram.imports import *
import django_telegram.tasks
import datetime as dt
import general.concurrency as concurrency
import general.urlencoding as urlencoding
from abc import abstractmethod
from django.db import transaction

FILE_ID_LENGTH = 100


class DjangoTelegramObject(models.Model):
    @classmethod
    def instantiate_from_instance(cls, instance, parent_fields=[], sent_to_bot=None):
        if instance is None:
            return None

        was_created = False

        if 'id' in dir(instance) or cls.__name__.lower() + '_id' in dir(instance):
            instance_id = getattr(instance, 'id') if 'id' in dir(instance) else getattr(instance,
                                                                                        cls.__name__.lower() + '_id')
            if cls == Message:
                if cls.objects.filter(**{'sent_to_bot': sent_to_bot, cls.__name__.lower() + '_id': instance_id}).count() == 1:
                    nmodel = cls.objects.get(**{'sent_to_bot': sent_to_bot, cls.__name__.lower() + '_id': instance_id})
                    was_created = False
                else:
                    nmodel = cls()
                    was_created = True

                nmodel.sent_to_bot = sent_to_bot
            else:
                if cls.objects.filter(**{cls.__name__.lower() + '_id': instance_id}).count() == 1:
                    nmodel = cls.objects.get(**{cls.__name__.lower() + '_id': instance_id})
                    was_created = False
                else:
                    nmodel = cls()
                    was_created = True
        else:
            nmodel = cls()
            was_created = True

        cls_fields = {field.name: field for field in cls._meta.get_fields()}
        field_values = {}
        many_to_many_field_values = {}

        for attr in dir(instance):
            if attr in cls_fields:
                field = cls_fields[attr]

                if isinstance(field, models.ForeignKey):
                    foreign = field.related_model.instantiate_from_instance(getattr(instance, attr), parent_fields + [
                        str(cls) + '.' + str(attr)], sent_to_bot=sent_to_bot)
                    field_values[attr] = foreign
                elif isinstance(field, models.ManyToManyField):
                    values = []
                    for sub_instance in getattr(instance, attr):
                        values.append(field.related_model.instantiate_from_instance(sub_instance, parent_fields + [
                            str(cls) + '.' + str(attr)], sent_to_bot=sent_to_bot))
                    many_to_many_field_values[attr] = values
                elif cls == Chat and attr == 'type':
                    for choice in constants.CHAT_TYPES.model_choices:
                        if choice[0] == getattr(instance, attr):
                            field_values[attr] = choice[1]
                elif cls == Chat and attr == 'id':
                    field_values['chat_id'] = getattr(instance, attr)
                elif cls == User and attr == 'id':
                    field_values['user_id'] = getattr(instance, attr)
                else:
                    field_values[attr] = getattr(instance, attr)
            else:
                pass

        if cls == Location:
            field_values['date'] = dt.datetime.now()

        if cls == Message and getattr(nmodel, 'location'):
            loc = getattr(nmodel, 'location')
            loc.message = nmodel
            loc.save()

        for attr, value in field_values.items():
            setattr(nmodel, attr, value)

        if not cls == Update:
            nmodel.save()

        for field in many_to_many_field_values:
            getattr(nmodel, field).set(many_to_many_field_values[field])

        if not cls == Update:
            nmodel.save()

        return nmodel

    class Meta:
        abstract = True


class User(DjangoTelegramObject):
    MAX_USERNAME_LENGTH = 30
    MAX_FIRST_NAME_LENGTH = 64
    MAX_LAST_NAME_LENGTH = 64
    MAX_LANGUAGE_CODE_LENGTH = 35

    user_id = models.IntegerField(unique=True)
    is_bot = models.BooleanField()
    first_name = models.CharField(max_length=MAX_FIRST_NAME_LENGTH)
    last_name = models.CharField(max_length=MAX_LAST_NAME_LENGTH, null=True)
    username = models.CharField(max_length=MAX_USERNAME_LENGTH, null=True, unique=True)
    language_code = models.CharField(max_length=MAX_LANGUAGE_CODE_LENGTH, null=True)

    def get_chat(self):
        return Chat.objects.get(chat_id=self.user_id)

    def __str__(self):
        if self.is_bot:
            return 'Bot User: %s, username: %s' % (self.first_name, self.username)
        return 'User: %s %s, username: %s' % (self.first_name, self.last_name, self.username)


class ChatPhoto(DjangoTelegramObject):
    small_file_id = models.CharField(max_length=FILE_ID_LENGTH)
    big_file_id = models.CharField(max_length=FILE_ID_LENGTH)


class Chat(DjangoTelegramObject):
    MAX_DESCRIPTION_LENGTH = 140
    MAX_DESCRIPTION_LENGTH = 255
    INVITE_LINK_LENGTH = 45
    MAX_STICKER_SET_NAME_LENGTH = 64

    chat_id = models.BigIntegerField(unique=True)
    type = models.IntegerField(choices=constants.CHAT_TYPES.model_choices)
    title = models.CharField(max_length=MAX_DESCRIPTION_LENGTH, null=True)
    username = models.CharField(max_length=User.MAX_USERNAME_LENGTH, null=True)
    first_name = models.CharField(max_length=User.MAX_FIRST_NAME_LENGTH, null=True)
    last_name = models.CharField(max_length=User.MAX_LAST_NAME_LENGTH, null=True)
    all_members_are_administrators = models.BooleanField(null=True)
    photo = models.ForeignKey(ChatPhoto, models.CASCADE, related_name='chats', null=True)
    description = models.CharField(max_length=MAX_DESCRIPTION_LENGTH, null=True)
    invite_link = models.CharField(max_length=INVITE_LINK_LENGTH, null=True)
    pinned = models.BooleanField(null=True)
    sticker_set_name = models.CharField(max_length=MAX_STICKER_SET_NAME_LENGTH, null=True)
    can_set_sticker_set = models.BooleanField(null=True)

    def get_user_state(self, user, bot, message=None):
        state_instances = StateInstance.objects.filter(chat=self, user=user, bot=bot, message=message)
        if state_instances.count() == 0:
            return None

        return state_instances[0]

    def is_private(self):
        return self.type == constants.CHAT_TYPES.PRIVATE

    def override_state(self, user, bot, state_instance):
        StateInstance.objects.filter(chat=self, user=user, bot=bot, message__isnull=True).delete()
        state_instance.save()

    def __str__(self):
        return "Chat: %s" % self.title


class PhotoSize(DjangoTelegramObject):
    file_id = models.CharField(max_length=FILE_ID_LENGTH)
    width = models.IntegerField()
    height = models.IntegerField()
    file_size = models.IntegerField(null=True)

    def __str__(self):
        return 'Photo: %s %ix%i' % (self.file_id, self.width, self.height)


class Location(DjangoTelegramObject):
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    message = models.ForeignKey('Message', models.CASCADE, related_name='locations', null=True)
    date = models.DateTimeField(null=True)

    def __str__(self):
        return 'lat: %s lng: %s' % (str(self.latitude), str(self.longitude))


class Contact(DjangoTelegramObject):
    MAX_MOBILE_LENGTH = 20

    phone_number = models.CharField(max_length=MAX_MOBILE_LENGTH)
    first_name = models.CharField(max_length=User.MAX_FIRST_NAME_LENGTH)
    last_name = models.CharField(max_length=User.MAX_LAST_NAME_LENGTH, null=True)
    user_id = models.IntegerField(null=True)
    vcard = models.TextField(null=True)


class Message(DjangoTelegramObject):
    MAX_TEXT_LENGTH = 4096
    MAX_CAPTION_LENGTH = 200

    message_id = models.IntegerField()
    from_user = models.ForeignKey(User, models.CASCADE, related_name='sent_messages', null=True)
    date = models.DateTimeField()
    chat = models.ForeignKey(Chat, models.CASCADE, related_name='messages')
    forward_from = models.ForeignKey(User, models.CASCADE, related_name='source_of_forwarded_messages', null=True)
    forward_from_chat = models.ForeignKey(Chat, models.CASCADE, related_name='source_of_forwarded_messages', null=True)
    forward_from_message_id = models.IntegerField(null=True)
    forward_date = models.DateTimeField(null=True)
    reply_to_message = models.ForeignKey('Message', models.CASCADE, related_name='replies', null=True)
    edit_date = models.DateTimeField(null=True)
    text = models.CharField(max_length=MAX_TEXT_LENGTH, null=True)
    # audio
    # document
    # animation
    # game
    photo = models.ManyToManyField(PhotoSize)
    # sticker
    # video
    # voice
    # video_note
    new_chat_members = models.ManyToManyField('User', related_name='added_to_chat_messages')
    caption = models.CharField(max_length=MAX_CAPTION_LENGTH, null=True)
    contact = models.ForeignKey(Contact, models.CASCADE, null=True)
    location = models.OneToOneField(Location, models.CASCADE, related_name='message_as_current_location', null=True)
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

    sent_by_bot = models.ForeignKey('Bot', models.DO_NOTHING, related_name='messages_sent', null=True)
    sent_to_bot = models.ForeignKey('Bot', models.DO_NOTHING, related_name='messages_received', null=True)

    deleted = models.BooleanField(default=False)

    def __str__(self):
        return 'Message from %s at %s' % (str(self.from_user), str(self.date))

    def forward(self, chat, **kwargs):
        return self.sent_by_bot.forward_message(self, chat, **kwargs)

    def reply(self, text, bot, **kwargs):
        return bot.message_chat(self.chat, text, reply_to=self, **kwargs)

    def delete_message(self):
        if not self.deleted:
            self.deleted = self.sent_by_bot.delete_message(self)
            self.save()
        return self.deleted

    def change_text(self, new_text, **kwargs):
        self.sent_by_bot.change_message_text(self, new_text, **kwargs)

    def change_photo(self, new_photo):
        self.sent_by_bot.change_message_photo(self, new_photo)

    def change_caption(self, caption):
        self.sent_by_bot.change_message_caption(self, caption)

    def change_reply_markup(self, reply_markup, **kwargs):
        self.sent_by_bot.change_reply_markup(self, reply_markup, **kwargs)

    def remove_inline_keyboard(self, **kwargs):
        self.sent_by_bot.change_reply_markup(self, telegram.InlineKeyboardMarkup([]), **kwargs)

    class Meta:
        unique_together = ('message_id', 'sent_to_bot')


class Bot(DjangoTelegramObject):
    BOT_TOKEN_LENGTH = 45
    MAX_BOT_NAME_LENGTH = 50

    name = models.CharField(max_length=MAX_BOT_NAME_LENGTH)
    token = models.CharField(max_length=BOT_TOKEN_LENGTH)

    enabled = models.BooleanField()

    default_private_state = models.ForeignKey('State', models.PROTECT, related_name='bots_with_private_default')
    default_group_state = models.ForeignKey('State', models.PROTECT, related_name='bots_with_group_default')

    initial_private_state = models.ForeignKey('State', models.PROTECT, related_name='bots_with_private_initial')
    initial_group_state = models.ForeignKey('State', models.PROTECT, related_name='bots_with_group_initial')

    def get_updater(self):
        return self.updater

    def get_user_id(self):
        return int(self.token.split(':')[0])

    def get_user(self):
        return User.objects.get(user_id=self.get_user_id())

    def get_username(self):
        return self.get_user().username

    def message_chat(self, chat, text, reply_to=None, **kwargs):
        reply_to_message_id = None
        if not reply_to is None:
            reply_to_message_id = reply_to.message_id

        return self.message_chat_from_id(chat.chat_id, text, reply_to_message_id=reply_to_message_id, **kwargs)

    def message_chat_from_id(self, chat_id, text, reply_to_message_id=None, **kwargs):
        message_instance = self.bot_instance.send_message(chat_id, text, reply_to_message_id=reply_to_message_id,
                                                          **kwargs)
        return self.log_message_sent(message_instance)

    def send_location_to_chat(self, chat, latitude, longitude, reply_to=None, **kwargs):
        reply_to_message_id = None
        if not reply_to is None:
            reply_to_message_id = reply_to.message_id

        return self.send_location_to_chat_from_id(chat.chat_id, latitude, longitude,
                                                  reply_to_message_id=reply_to_message_id, **kwargs)

    def send_location_to_chat_from_id(self, chat_id, latitude, longitude, reply_to_message_id=None, **kwargs):
        message_instance = self.bot_instance.send_location(chat_id, float(latitude), float(longitude),
                                                           reply_to_message_id=reply_to_message_id, **kwargs)
        return self.log_message_sent(message_instance)

    def send_photo_to_chat(self, chat, photo, caption=None, reply_to=None, **kwargs):
        reply_to_message_id = None
        if not reply_to is None:
            reply_to_message_id = reply_to.message_id

        return self.send_photo_to_chat_from_id(chat.chat_id, photo, caption=caption,
                                               reply_to_message_id=reply_to_message_id, **kwargs)

    def send_photo_to_chat_from_id(self, chat_id, photo, caption=None, reply_to_message_id=None, **kwargs):
        message_instance = self.bot_instance.send_photo(chat_id, photo, caption=caption,
                                                        reply_to_message_id=reply_to_message_id, **kwargs)
        return self.log_message_sent(message_instance)

    def change_message_text(self, message, new_text, **kwargs):
        message = Message.instantiate_from_instance(self.bot_instance.edit_message_text(chat_id=message.chat.chat_id,
                                                                                        message_id=message.message_id,
                                                                                        text=new_text,
                                                                                        **kwargs))
        return message

    def change_message_photo(self, message, new_photo):
        message = Message.instantiate_from_instance(self.bot_instance.edit_message_media(chat_id=message.chat.chat_id,
                                                                                         message_id=message.message_id,
                                                                                         media=telegram.InputMediaPhoto(
                                                                                             new_photo)))
        return message

    def change_message_caption(self, message, caption):
        message = Message.instantiate_from_instance(self.bot_instance.edit_message_caption(chat_id=message.chat.chat_id,
                                                                                           message_id=message.message_id,
                                                                                           caption=caption))
        return message

    def change_reply_markup(self, message, reply_markup, **kwargs):
        message = Message.instantiate_from_instance(
            self.bot_instance.edit_message_reply_markup(chat_id=message.chat.chat_id,
                                                        message_id=message.message_id,
                                                        reply_markup=reply_markup,
                                                        **kwargs)
        )

        return message

    def send_video_to_chat(self, chat, video, reply_to=None, **kwargs):
        reply_to_message_id = None
        if not reply_to is None:
            reply_to_message_id = reply_to.message_id

        return Message.instantiate_from_instance(
            self.bot_instance.send_video(chat_id=chat.chat_id, video=video, reply_to_message_id=reply_to_message_id,
                                         **kwargs)
        )

    def get_from_instance(bot_instance):
        if bot_manager.bots_initialized:
            return bot_manager.bots[bot_instance.token]

        return Bot.objects.get(token=bot_instance.token)

    def forward_message(self, message, chat, **kwargs):
        return self.forward_message_from_ids(chat_id=chat.chat_id,
                                             from_chat_id=message.chat.chat_id,
                                             message_id=message.message_id,
                                             **kwargs)

    def forward_message_from_ids(self, chat_id, from_chat_id, message_id, **kwargs):
        message_instance = self.bot_instance.forward_message(chat_id=chat_id,
                                                             from_chat_id=from_chat_id,
                                                             message_id=message_id,
                                                             **kwargs)

        return self.log_message_sent(message_instance)

    def edit_message_reply_markup(self, message, reply_markup, **kwargs):
        message = Message.instantiate_from_instance(self.bot_instance.edit_message_reply_markup(chat_id=message.chat.chat_id,
                                                                                        message_id=message.message_id,
                                                                                        reply_markup=reply_markup,
                                                                                        **kwargs))
        return message

    def delete_message(self, message):
        return self.bot_instance.delete_message(chat_id=message.chat.chat_id, message_id=message.message_id)

    def get_click_to_telegram_link(self, start_payload=None):
        link = "https://t.me/%s" % self.get_user().username

        if start_payload:
            link += '?start=%s' % urlencoding.url_encode(start_payload)

        return link

    def log_message_sent(self, message_instance):
        message = Message.instantiate_from_instance(message_instance)
        message.sent_by_bot = self
        message.save()
        return message

    def load_bot_instance(self):
        if self.token:
            self.updater = telegram.ext.Updater(self.token)
            self.bot_instance = self.updater.bot

    def __str__(self):
        return 'Bot: %s' % self.name


def bot_post_init(sender, instance, **kwargs):
    instance.load_bot_instance()


post_init.connect(bot_post_init, sender=Bot)


class Update(DjangoTelegramObject):
    update_id = models.IntegerField(unique=True)

    effective_chat = models.ForeignKey('Chat', models.CASCADE)
    effective_message = models.ForeignKey('Message', models.CASCADE, null=True)
    effective_user = models.ForeignKey('User', models.CASCADE)

    def __str__(self):
        return 'Update: %s %s %s' % (self.effective_chat, self.effective_user, self.effective_message)


class State(models.Model):
    MAX_STATE_NAME_LENGTH = 50
    MAX_STATE_FUNCTION_PATH_LENGTH = 200

    name = models.CharField(max_length=MAX_STATE_NAME_LENGTH)
    function_path = models.CharField(max_length=MAX_STATE_FUNCTION_PATH_LENGTH)

    def __str__(self):
        return self.name

    def instantiate(self, chat, user, bot, message=None, kwargs={}):
        return StateInstance(state=self, chat=chat, user=user, bot=bot, message=message, kwargs_json=json.dumps(kwargs))

    def load_state_function(self):
        if self.function_path:
            func = load_from_path(self.function_path)
            self.state_function = func


def state_post_init(sender, instance, **kwargs):
    instance.load_state_function()


post_init.connect(state_post_init, sender=State)


class StateInstance(models.Model):
    state = models.ForeignKey('State', models.CASCADE, related_name='instances')
    chat = models.ForeignKey('Chat', models.CASCADE, related_name='state_instances')
    user = models.ForeignKey('User', models.CASCADE, related_name='state_instances')
    bot = models.ForeignKey('Bot', models.CASCADE, related_name='state_instances')
    message = models.ForeignKey('Message', models.CASCADE, related_name='state_instances', null=True, blank=True)
    kwargs_json = models.TextField()

    def __str__(self):
        return "%s state instance (%s, %s, %s, %s)" % (
        str(self.state), str(self.chat), str(self.user), str(self.bot), self.kwargs_json)

    def state_function_wrapper(self, bot, update):
        return self.state.state_function(bot, update, **self.kwargs)

    def load_kwargs(self):
        if self.kwargs_json:
            self.kwargs = json.loads(self.kwargs_json)

    def dumps_kwargs(self):
        if self.kwargs:
            self.kwargs_json = json.dumps(self.kwargs)

    class Meta:
        unique_together = ('chat', 'user', 'bot', 'message')


def state_instance_post_init(sender, instance, **kwargs):
    instance.load_kwargs()


post_init.connect(state_instance_post_init, sender=StateInstance)


class Handler(models.Model):
    MAX_HANDLER_NAME_LENGTH = 50
    MAX_HANDLER_PATH_LENGTH = 200

    name = models.CharField(max_length=MAX_HANDLER_NAME_LENGTH)
    class_path = models.CharField(max_length=MAX_HANDLER_PATH_LENGTH)
    filter_path = models.CharField(max_length=MAX_HANDLER_PATH_LENGTH, blank=True, null=True)
    function_path = models.CharField(max_length=MAX_HANDLER_PATH_LENGTH)
    kwargs_json = models.TextField()

    def __str__(self):
        return self.name

    def load_handler_function(self):
        if self.function_path:
            func = load_from_path(self.function_path)
            self.handler_function = func

    def load_class_path(self):
        if self.class_path:
            cls = load_from_path(self.class_path)
            self.handler_class = cls

    def load_filter_path(self):
        if self.filter_path:
            filter = load_from_path(self.filter_path)
            self.filter = filter

    def load_kwargs(self):
        if self.kwargs_json:
            self.kwargs = json.loads(self.kwargs_json)

    def dumps_kwargs(self):
        if self.kwargs:
            self.kwargs_json = json.dumps(self.kwargs)


def handler_post_init(sender, instance, **kwargs):
    instance.load_handler_function()
    instance.load_class_path()
    instance.load_kwargs()

    try:
        instance.load_filter_path()
    except:
        pass


post_init.connect(handler_post_init, sender=Handler)


def handler_pre_save(sender, instance, **kwargs):
    instance.load_handler_function()
    instance.load_class_path()
    instance.load_kwargs()
    instance.load_filter_path()


pre_save.connect(handler_pre_save, sender=Handler)


class HandlerInstance(telegram.ext.Handler, models.Model):
    handler = models.ForeignKey('Handler', models.CASCADE, related_name='instances')
    bot = models.ForeignKey('Bot', models.CASCADE, related_name='handler_instances')
    group = models.IntegerField()
    add_order = models.IntegerField()

    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)

    def handle_update(self, bot, update, *args, **kwargs):
        bot = Bot.get_from_instance(bot)
        update = Update.instantiate_from_instance(update, sent_to_bot=bot)
        return self.handler.handler_function(bot, update, *args, **kwargs)

    def load_handler(self):
        try:
            kwargs = self.handler.kwargs.copy()
            if self.handler.filter_path is not None:
                kwargs['filters'] = self.handler.filter
            kwargs['callback'] = self.handle_update

            self.telegram_handler = self.handler.handler_class(**kwargs)
        except HandlerInstance.handler.RelatedObjectDoesNotExist as e:
            print(e)
            pass
        except AttributeError as e:
            print(e)
            pass

    # def __call__(self, *args, **kwargs):
    #     self.handle_update(*args, **kwargs)

    def __str__(self):
        return '%s instance with bot %s.' % (str(self.handler), str(self.bot))


def handler_instance_post_init(sender, instance, **kwargs):
    instance.load_handler()


post_init.connect(handler_instance_post_init, sender=HandlerInstance)

class MessageModel(models.Model, concurrency.lockable):
    sent_for_sending = models.DateTimeField(null=True)
    sent = models.BooleanField(default=False)

    def send(self, use_celery=True):
        lck = self.get_lock()

        if not use_celery:
            self.send_message()

        if not self.sent:
            self.sent_for_sending = dt.datetime.now()
            self.save()

            cls = get_fullname(self)
            id = self.id
            django_telegram.tasks.send_message_model.apply_async(args=[cls, id], queue='telegram_queue')

        self.release_lock()

    class Meta:
        abstract = True

post_init.connect(telegram_client_api_instance_post_init, sender=TelegramClientAPI)

import django_telegram.bot_manager as bot_manager
import django_telegram.client_api as client_api
