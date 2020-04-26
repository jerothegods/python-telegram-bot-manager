
chat_creation_welcome_message = "Hello from %s. This chat's id is %d."
def get_chat_creation_welcome_message(bot, chat):
    return chat_creation_welcome_message % (bot.name, chat.chat_id)

group_chat_added_welcome_message = "%s has been added to this group. This chat's id is %d."
def get_group_chat_added_welcome_message(bot, chat):
    return group_chat_added_welcome_message % (bot.name, chat.chat_id)

chat_id_message = "The id of this chat is: %d"
def get_chat_id_message(chat):
    return chat_id_message % chat.chat_id

def get_group_creation_message():
    return  "Welcome to the group!"