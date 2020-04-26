import process_manager.process

if __name__=='__main__':
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Butlers.settings")
    import django
    django.setup()

import django_telegram.models as telegram_models
import logging
import Butlers.butlers_telegram

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

bots_initialized = False
bots = {}
enabled_bots = {}
Updaters = {}

jeremy_chat = telegram_models.Chat.objects.first()

def initialize_bots():
    global bots_initialized

    if bots_initialized:
        return

    bots_initialized = True
    for bot in telegram_models.Bot.objects.all():
        bots[bot.token] = bot
        if bot.enabled:
            updater = bot.get_updater()

            for handler_instance in bot.handler_instances.all().order_by('group', 'add_order'):
                print('Adding %s' % str(handler_instance))
                updater.dispatcher.add_handler(handler_instance.telegram_handler, group=handler_instance.group)

            updater.start_polling()
            Updaters[bot] = updater
            enabled_bots[bot.token] = bot

            print(bot.name, 'started.')
        else:
            print(bot.name, 'not started.')
    bots_initialized = True

def shutdown_bots():
    for token in enabled_bots:
        bot = enabled_bots[token]
        Updaters[bot].stop()

if __name__ == '__main__':
    Butlers.butlers_telegram.message_system_alerts('Starting bot manager.')
    initialize_bots()

# if __name__=='__main__':
#     initialize_bots()
#     while input()!='quit':
#         pass
#     shutdown_bots()
