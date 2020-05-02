import logging

from telegram import (InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler, StringRegexHandler)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


### States ###

# State definitions for top level conversation
SELECTING_ACTION, RECORD_SALE, RECORD_EXPENSE, RECORD_PURCHASE = map(chr, range(4))

# State definitions for sale level conversation
SALE_DATE, SALE_AMOUNT, SALE_RECORD_DONE = map(chr, range(4,7))

# Meta states
DONE = map(chr, range(7, 8))

# Shortcut for ConversationHandler.END
END = ConversationHandler.END

# Helper Constants
START_OVER = map(chr, range(8,9))


### Callbacks ###

# Top level conversation callbacks
def start(update, context):
    """Select an action: Adding parent/child or show data."""
    text = 'You may add a new record. To abort, simply type /done.'
    buttons = [[
        InlineKeyboardButton(text='Record Sale', callback_data=str(RECORD_SALE)),
        InlineKeyboardButton(text='Record Purchase', callback_data=str(RECORD_PURCHASE))
    ], [
        InlineKeyboardButton(text='Record Expense', callback_data=str(RECORD_EXPENSE)),
        InlineKeyboardButton(text='Done', callback_data=str(DONE))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    #If we're starting over we don't need do send a new message
    if context.user_data.get(not START_OVER):
        update.message.reply_text(text=text, reply_markup=keyboard)
    else:
        update.message.reply_text('Hi, I\'m ChumaFinanceBot and here to help.')
        update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return SELECTING_ACTION


def sale_date(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Type the date of the sale.")
    update.callback_query.answer()
    return SALE_DATE
    

def sale_amount(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Type the amount of the sale.")
    return SALE_AMOUNT

def sale_record_done(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sale Recorded!")
    start(update, context)
    return END

def record_expense(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Expense Recorded")
    update.callback_query.answer()
    return DONE

def record_purchase(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Purchase Recorded")
    update.callback_query.answer()
    return DONE

def done(update, context):
    update.callback_query.answer()

    # text = 'See you around!'
    # update.callback_query.edit_message_text(text=text)

    context.bot.send_message(chat_id=update.effective_chat.id, text="Okay, bye")

    return END


### Dispatcher & Handlers ###

def main():

    updater = Updater("TOKEN", use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Sale level conversation handler
    sale_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(sale_date, pattern='^' + str(RECORD_SALE) + '$')
            ],

        states={
            SALE_DATE: [
                MessageHandler(Filters.text, sale_amount)
            ],
            SALE_AMOUNT:[
                MessageHandler(Filters.text, sale_record_done)
            ],
            SALE_RECORD_DONE:[
                
            ],
        },

        fallbacks=[
            CommandHandler('done', done)
            ],
    )

    # Set up top level ConversationHandler (selecting action)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            SELECTING_ACTION: [
                sale_conv_handler,
                CallbackQueryHandler(record_expense, pattern='^' + str(RECORD_EXPENSE) + '$'),
                CallbackQueryHandler(record_purchase, pattern='^' + str(RECORD_PURCHASE) + '$'),
                CallbackQueryHandler(done, pattern='^' + str(DONE) + '$')
            ]
        },

        fallbacks=[CommandHandler('done', done)],
    )

    dp.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()