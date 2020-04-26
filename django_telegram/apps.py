from django.apps import AppConfig
import os

launch_bots = os.environ.get('launch_telegram_bots') == '1'

class DjangoTelegramConfig(AppConfig):
    name = 'django_telegram'
    verbose_name = 'Django Telegram'

    def ready(self):
        import django_telegram.states as states

        states.load_states()

        return
        import django_telegram.bot_manager as bot_manager


        if launch_bots and False:
            print('Initializing Telegram bots.')
            bot_manager.initialize_bots()
        else:
            print('Not initializing Telegram bots (no launch_telegram_bots env flag).')
