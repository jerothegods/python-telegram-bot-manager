from telethon import sync, TelegramClient, functions, types
import django_telegram.models as telegram_models
import django_telegram.strings as strings

group_manage_mobile_number = '+27748183922'
group_manager_bot = telegram_models.Bot.objects.get(name='Group Manager')

def add_contact_from_mobile(client, first_name, mobile, last_name=''):
    with client.telegram_client as client:
        result = client(functions.contacts.ImportContactsRequest(
            [types.InputPhoneContact(
                client_id=0,
                phone=mobile,
                first_name=first_name,
                last_name=last_name
            )]
        ))
        return result

def get__users_in_chat(client, chat):
    with client.telegram_client as client:
        result = client(functions.messages.GetFullChatRequest(
            chat_id=chat.chat_id,
        ))

        return result

def is_user_in_chat(client, chat, user):
    user_ids = [user.id for user in get__users_in_chat(client, chat).users]
    return user.user_id in user_ids

def create__group_from_mobiles(client, title, numbers):
    numbers += [group_manager_bot.get_username()]

    with client.telegram_client as client:
        result = client(functions.messages.CreateChatRequest(
            users=numbers,
            title=title
        ))

        chat_id = result.updates[1].participants.chat_id
        message = group_manager_bot.message_chat_from_id(-chat_id, strings.get_group_creation_message())

        return message.chat

def add_users_to_chat(client, chat, users, fwd_limit=0):
    with client.telegram_client as client:
        for user in users:
            result = client(functions.messages.AddChatUserRequest(
                chat_id=chat.chat_id,
                user_id=user.user_id,
                fwd_limit=fwd_limit,
            ))

def remove_users_from_chat(client, chat, users):
    with client.telegram_client as client:
        for user in users:
            result = client(functions.messages.DeleteChatUserRequest(
                chat_id=chat.chat_id,
                user_id=user.user_id,
            ))
            return result