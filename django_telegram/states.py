import django_telegram.models as telegram_models

STATE = {}

def do_nothing_state(bot, update):
    return STATE['Do Nothing'].instantiate(update.effective_chat, update.effective_user, bot)

def load_states():
    STATE['Do Nothing'] = telegram_models.State.objects.get(name='Do Nothing')
