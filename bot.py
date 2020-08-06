import os
import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import handlers
import settings

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

log = logging.getLogger(__name__)

PORT = int(os.environ.get('PORT', '8443'))


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(token=settings.BOT_API_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", handlers.start))
    dp.add_handler(CommandHandler("help", handlers.help))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handlers.echo))

    updater.start_webhook(listen='0.0.0.0',
                          port=8443,
                          url_path=settings.BOT_API_TOKEN,
                          key='private.key',
                          cert='cert.pem',
                          webhook_url='https://18.133.32.222:8443/{}'.format(settings.BOT_API_TOKEN))

    updater.bot.set_webhook('https://18.133.32.222:8443/{}'.format(settings.BOT_API_TOKEN))
    updater.idle()


if __name__ == '__main__':
    main()