import os

from telegram.ext import Updater, CommandHandler, InlineQueryHandler, CallbackQueryHandler, \
    MessageHandler, Filters, ConversationHandler, Handler

import handlers
import settings
import database

from utility import setup_notification_jobs

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
    dp.add_handler(ConversationHandler(
        entry_points=[
            CommandHandler(
                command="start",
                callback=handlers.request_location_handler,
                filters=Filters.private &
                        Filters.regex(settings.CALLBACK_DATA_REGEX['DEEPLINKING_LINK']))
        ],
        states={
            settings.VERIFY_LOCATION_CONV_ID: [MessageHandler(
                filters=Filters.location, callback=handlers.request_location_verify_handler)]

        },
        fallbacks=[
            MessageHandler(
                filters=Filters.regex('Cancel'), callback=handlers.request_location_failed_handler)
        ]))

    dp.add_handler(CommandHandler(
        command="start", callback=handlers.start_command,
        filters=Filters.private &
                ~Filters.regex(settings.CALLBACK_DATA_REGEX['DEEPLINKING_LINK'])))
    dp.add_handler(CommandHandler(
        command="stats", callback=handlers.stats_command, filters=Filters.private))
    dp.add_handler(CommandHandler(
        command="invite_contest", callback=handlers.invite_contest_callback, filters=Filters.private))
    dp.add_handler(CommandHandler(
        command="reflink", callback=handlers.referral_link_command, filters=Filters.private))
    dp.add_handler(CommandHandler(
        command="chats", callback=handlers.chats_command_handler, filters=Filters.private))

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
    dp.add_handler(CallbackQueryHandler(callback=handlers.change_timezone_callback,
                                        pattern=settings.CALLBACK_DATA_REGEX['CHANGE_TIMEZONE']))
    dp.add_handler(CallbackQueryHandler(callback=handlers.send_notification_callback,
                                        pattern=settings.CALLBACK_DATA_REGEX['SEND_NOTIFICATION']))
    dp.add_handler(CallbackQueryHandler(callback=handlers.drop_stats_callback,
                                        pattern=settings.CALLBACK_DATA_REGEX['DROP_STATS']))
    dp.add_handler(CallbackQueryHandler(callback=handlers.settings_back_callback,
                                        pattern=settings.CALLBACK_DATA_REGEX['SETTINGS_BACK']))
    dp.add_handler(CallbackQueryHandler(callback=handlers.pick_language_callback,
                                        pattern=settings.CALLBACK_DATA_REGEX['PICK_LANGUAGE']))
    dp.add_handler(CallbackQueryHandler(callback=handlers.pick_timezone_callback,
                                        pattern=settings.CALLBACK_DATA_REGEX['PICK_TIMEZONE']))
    dp.add_handler(CallbackQueryHandler(callback=handlers.generate_ref_link_callback,
                                        pattern=settings.CALLBACK_DATA_REGEX['GENERATE_REF_LINK']))

    dp.add_handler(InlineQueryHandler(handlers.inline_query_handler))

    dp.add_handler(MessageHandler(Filters.status_update.chat_created, handlers.chat_created_handler))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, handlers.new_chat_members_handler))
    dp.add_handler(MessageHandler(Filters.status_update.left_chat_member, handlers.left_chat_member_handler))

    dp.add_error_handler(handlers.error)

    if settings.DEBUG is False:
        setup_notification_jobs(job_queue=updater.job_queue, callback=handlers.on_notification_callback)

    database.database_startup()

    if settings.DEBUG:
        updater.start_polling()
    else:
        updater.start_webhook(listen='0.0.0.0',
                              port=settings.SERVER_WEBHOOK_PORT,
                              url_path=settings.BOT_API_TOKEN,
                              key='private.key',
                              cert='public.pem',
                              webhook_url='https://{}:{}/{}'.format(
                                  settings.SERVER_WEBHOOK_IP, settings.SERVER_WEBHOOK_PORT, settings.BOT_API_TOKEN))

    #updater.job_queue.run_once(when=1, callback=handlers.on_notification_callback, context="-1001340533305")

    updater.idle()
    database.database_closeup()


if __name__ == '__main__':
    main()
