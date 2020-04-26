import django_telegram.strings as strings
import django_telegram.constants as constants
import telegram.ext


master_message_receiver_handler_filter = telegram.ext.Filters.all
def master_message_receiver_handler(bot, update):
    message = update.effective_message
    message.sent_to_bot = bot
    message.save()

new_chat_created_handler_filter = telegram.ext.Filters.status_update.chat_created
#Use this for group creation and new chat creation
def new_chat_created_handler(bot, update):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == constants.CHAT_TYPES.PRIVATE:
        state = bot.initial_private_state
    else:
        state = bot.initial_group_state

    state_instance = state.instantiate(chat, user, bot)
    state_instance.save()

    bot.message_chat(chat, strings.get_chat_creation_welcome_message(bot, update.effective_message.chat))

bot_added_to_group_handler_filter = telegram.ext.Filters.status_update.new_chat_members
def bot_added_to_group_handler(bot, update):
    for user in update.effective_message.new_chat_members.all():
        if user.user_id == int(bot.token.split(':')[0]):
            chat = update.effective_chat

            bot.message_chat(update.effective_chat, strings.get_group_chat_added_welcome_message(bot, update.effective_chat))

            if chat.type == constants.CHAT_TYPES.PRIVATE:
                state = bot.initial_private_state
            else:
                state = bot.initial_group_state

            state_instance = state.instantiate(chat, user, bot)
            state_instance.save()

            return

state_handler_filter = telegram.ext.Filters.all
def state_handler(bot, update):
    chat = update.effective_chat
    user = update.effective_user

    state_instance = chat.get_user_state(user, bot)

    if state_instance is None:
        if chat.is_private():
            state = bot.default_private_state
        else:
            state = bot.default_group_state
        state_instance = state.instantiate(chat, user, bot)
        state_instance.save()

    print('Handling user request in state', state_instance)

    new_state = state_instance.state_function_wrapper(bot, update)

    state_instance.delete()
    new_state.save()

    print('User now in state', new_state)

chat_id_handler_filter = telegram.ext.Filters.all
def chat_id_handler(bot, update):
    print("Received chatid request")
    chat = update.effective_chat
    bot.message_chat(chat, strings.get_chat_id_message(update.effective_chat))