import os
import logging

from telegram.ext import Updater, CommandHandler, InlineQueryHandler, CallbackQueryHandler,\
    MessageHandler, Filters

import handlers
import settings
import utility

from utility import log

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
    dp.add_handler(CommandHandler("start", handlers.start_command, filters=Filters.private))
    dp.add_handler(CommandHandler("chats", handlers.chats_command_handler, filters=Filters.private))

    dp.add_handler(CallbackQueryHandler(handlers.pick_chat_callback, settings.CALLBACK_DATA_REGEX['PICK_CHAT']))
    dp.add_handler(CallbackQueryHandler(handlers.enable_chat_callback, settings.CALLBACK_DATA_REGEX['ENABLE_CHAT']))
    dp.add_handler(CallbackQueryHandler(handlers.disable_chat_callback, settings.CALLBACK_DATA_REGEX['DISABLE_CHAT']))
    dp.add_handler(CallbackQueryHandler(handlers.enable_notifications_callback, settings.CALLBACK_DATA_REGEX['ENABLE_NOTIFICATIONS']))
    dp.add_handler(CallbackQueryHandler(handlers.disable_notifications_callback, settings.CALLBACK_DATA_REGEX['DISABLE_NOTIFICATIONS']))
    dp.add_handler(CallbackQueryHandler(handlers.change_language_callback, settings.CALLBACK_DATA_REGEX['CHANGE_LANGUAGE']))
    dp.add_handler(CallbackQueryHandler(handlers.pick_language_callback, settings.CALLBACK_DATA_REGEX['PICK_LANGUAGE']))
    dp.add_handler(CallbackQueryHandler(handlers.send_stats_callback, settings.CALLBACK_DATA_REGEX['SEND_STATS']))
    dp.add_handler(CallbackQueryHandler(handlers.invite_message_callback, settings.CALLBACK_DATA_REGEX['INVITE_MESSAGE']))

    dp.add_handler(InlineQueryHandler(handlers.inline_query_handler))

    dp.add_handler(MessageHandler(Filters.status_update.chat_created, handlers.chat_created_handler))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, handlers.new_chat_members_handler))
    dp.add_handler(MessageHandler(Filters.status_update.left_chat_member, handlers.left_chat_member_handler))

    updater.start_polling()

    """
    updater.start_webhook(listen='0.0.0.0',
                          port=8443,
                          url_path=settings.BOT_API_TOKEN,
                          key='private.key',
                          cert='cert.pem',
                          webhook_url='https://18.133.32.222:8443/{}'.format(settings.BOT_API_TOKEN))

    """
    updater.idle()


if __name__ == '__main__':
    main()