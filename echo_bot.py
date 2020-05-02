import logging
from telegram.ext import Updater, MessageHandler, Filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def echo(update, context):
    update.message.reply_text(update.message.text)

def main():

    updater = Updater("1217645409:AAErW7O6IhbGwKmjKOS7zp2I8vbG5ovmwGE", use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    echo_handler = MessageHandler(Filters.text, echo)

    dp.add_handler(echo_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()