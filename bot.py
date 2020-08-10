import os
import logging

from telegram.ext import Updater, CommandHandler, InlineQueryHandler, CallbackQueryHandler,\
    MessageHandler, Filters

import handlers
import settings
import utility
import database

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
    dp.add_handler(CommandHandler(command="start",
                                  callback=handlers.start_deeplinking_command,
                                  filters=Filters.private &
                                          Filters.regex(settings.CALLBACK_DATA_REGEX['DEEP_LINKING_LINK'])))
    dp.add_handler(CommandHandler(command="start",
                                  callback=handlers.start_command,
                                  filters=Filters.private))

    dp.add_handler(CommandHandler("chats", handlers.chats_command_handler, filters=Filters.private))

    dp.add_handler(CallbackQueryHandler(callback=handlers.pick_chat_callback,
                                        pattern=settings.CALLBACK_DATA_REGEX['PICK_CHAT']))
    dp.add_handler(CallbackQueryHandler(callback=handlers.enable_chat_callback,
                                        pattern=settings.CALLBACK_DATA_REGEX['ENABLE_CHAT']))
    dp.add_handler(CallbackQueryHandler(callback=handlers.disable_chat_callback,
                                        pattern=settings.CALLBACK_DATA_REGEX['DISABLE_CHAT']))
    dp.add_handler(CallbackQueryHandler(callback=handlers.enable_notifications_callback,
                                        pattern=settings.CALLBACK_DATA_REGEX['ENABLE_NOTIFICATIONS']))
    dp.add_handler(CallbackQueryHandler(callback=handlers.disable_notifications_callback,
                                        pattern=settings.CALLBACK_DATA_REGEX['DISABLE_NOTIFICATIONS']))
    dp.add_handler(CallbackQueryHandler(callback=handlers.change_language_callback,
                                        pattern=settings.CALLBACK_DATA_REGEX['CHANGE_LANGUAGE']))
    dp.add_handler(CallbackQueryHandler(callback=handlers.send_notification_callback,
                                        pattern=settings.CALLBACK_DATA_REGEX['SEND_NOTIFICATION']))
    dp.add_handler(CallbackQueryHandler(callback=handlers.settings_back_callback,
                                        pattern=settings.CALLBACK_DATA_REGEX['SETTINGS_BACK']))
    dp.add_handler(CallbackQueryHandler(callback=handlers.pick_language_callback,
                                        pattern=settings.CALLBACK_DATA_REGEX['PICK_LANGUAGE']))
    dp.add_handler(CallbackQueryHandler(callback=handlers.generate_ref_link_callback,
                                        pattern=settings.CALLBACK_DATA_REGEX['GENERATE_REF_LINK']))

    dp.add_handler(InlineQueryHandler(handlers.inline_query_handler))

    dp.add_handler(MessageHandler(Filters.status_update.chat_created, handlers.chat_created_handler))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, handlers.new_chat_members_handler))
    dp.add_handler(MessageHandler(Filters.status_update.left_chat_member, handlers.left_chat_member_handler))

    database.database_startup()

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
    database.database_closeup()

if __name__ == '__main__':
    main()