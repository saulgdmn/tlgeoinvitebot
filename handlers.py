from uuid import uuid4

from telegram import Update
from telegram import ReplyKeyboardRemove
from telegram import InlineQueryResultArticle, InputTextMessageContent

from telegram.ext import Updater, CallbackContext, ConversationHandler

import settings
from utility import *
from database import SpectatedChat, ReferralRecord


def error(update, context):
    context.bot.send_message(
        chat_id=settings.DEVELOPER_CHAT_ID, text=format_error_message(update, context), parse_mode='HTML')
    raise


def stats_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    for chat in SpectatedChat.get_chats_list(enabled=True):
        if is_member(bot=context.bot, chat_id=chat.chat_id, user_id=user_id):
            update.effective_chat.send_message(text=format_personal_stats(chat, user_id), parse_mode='HTML')


def referral_link_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    for chat in SpectatedChat.get_chats_list(enabled=True):
        if is_member(bot=context.bot, chat_id=chat.chat_id, user_id=user_id):
            update.effective_chat.send_message(
                text=get_chat_lang(chat).get('referral_link_text').format(
                    referral_link=generate_deeplinking_link(chat_id=chat.chat_id, user_id=user_id),
                    chat_title=chat.title),
                parse_mode='HTML', disable_web_page_preview=True)


def start_command(update: Update, context: CallbackContext):
    """Handle the command /start issued in private chat."""

    update.effective_chat.send_message(
        text=get_lang('en').get('start_text').format(
            invite_button_text=get_lang('en').get('invite_button_text')),
        reply_markup=generate_start_markup(), parse_mode='HTML')

@administrators_only
def invite_contest_callback(update: Update, context: CallbackContext):
    for chat in SpectatedChat.get_chats_list(enabled=True):
        update.effective_chat.send_message(text='Generating invite contest for <b>{}</b>'.format(chat.title), parse_mode='HTML')
        for text in format_invite_contest_texts(bot=context.bot, chat=chat):
            update.effective_chat.send_message(text=text, parse_mode='HTML')


def request_location_handler(update: Update, context: CallbackContext):
    """Handle the command /start issued in private chat."""

    chat_id = context.match.groupdict().get('chat_id', None)
    user_id = context.match.groupdict().get('user_id', None)

    context.chat_data['chat_id'] = chat_id
    context.chat_data['user_id'] = user_id

    chat = SpectatedChat.get_by_chat_id(chat_id)

    update.effective_chat.send_message(
        text=get_chat_lang(chat).get('request_location_text').format(
            request_location_button_text=get_lang('en').get('request_location_button_text')),
        reply_markup=generate_request_location_markup(chat), parse_mode='HTML')

    return settings.VERIFY_LOCATION_CONV_ID


def request_location_verify_handler(update: Update, context: CallbackContext):

    invited_chat_id = context.chat_data.get('chat_id', None)
    invited_chat = SpectatedChat.get_by_chat_id(invited_chat_id)
    chat_lang = get_chat_lang(invited_chat)

    if update.effective_message.forward_from is not None:
        update.effective_chat.send_message(
            text='Don\'t scam!', reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    location = update.effective_message.location

    if verify_location(location.longitude, location.latitude, invited_chat) is False:
        update.effective_chat.send_message(
            text=chat_lang.get('request_location_unavailable_text'), reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    bot = context.bot
    message = update.effective_message

    from_user = context.chat_data.get('user_id', None)
    to_user = message.from_user.id

    # check if inviting user is an invited user
    if int(from_user) == int(to_user):
        update.effective_chat.send_message(text=chat_lang.get('cant_invite_yourself_text'))
        return ConversationHandler.END

    # check if an invited user is already a member of the chat
    if is_member(bot=bot, chat_id=invited_chat_id, user_id=to_user):
        update.effective_chat.send_message(text=chat_lang.get('is_already_member_text'))
        return ConversationHandler.END

    # check if a user referral record for an invited user is already exists
    # and create if not
    record = ReferralRecord.get_by_to_user(chat_id=invited_chat_id, to_user=to_user)
    if record is None:
        record = ReferralRecord.add(
            chat_id=invited_chat_id, to_user_chat_id=message.chat.id, from_user=from_user, to_user=to_user)

    update.effective_chat.send_message(
        reply_markup=generate_join_markup(invited_chat),
        text=chat_lang.get('request_location_success_text').format(
            chat_title=invited_chat.title,
            join_button_text=chat_lang.get('join_button_text')),
        parse_mode='HTML')

    return ConversationHandler.END


def request_location_failed_handler(update: Update, context: CallbackContext):
    chat_id = context.chat_data.get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    update.effective_chat.send_message(
        text=get_chat_lang(chat).get('request_location_failed_text'), reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


@administrators_only
def chats_command_handler(update: Update, context: CallbackContext):
    """Handle the command /chats issued in a private chat."""

    chats = SpectatedChat.get_chats_list()
    log.info(chats)
    if chats is None:
        update.effective_chat.send_message(text='There are no spectated chats!')
        return

    update.effective_chat.send_message(text='Choose a chat.', reply_markup=generate_chats_markup(chats))


def pick_chat_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('pick_chat_callback chat not founded: {}'.format(chat_id))
        return

    update.effective_message.edit_text(
        text=format_chat_settings_message(chat), parse_mode='HTML', reply_markup=generate_chat_settings_markup(chat))


def enable_chat_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('enable_chat_callback chat not founded: {}'.format(chat_id))
        return

    if context.bot.id not in [admin.user.id for admin in context.bot.get_chat_administrators(chat_id=chat.chat_id)]:
        update.callback_query.answer(
            text='Not enough rights to export chat invite link.\nPlease, make me an administrator', show_alert=True)
        return

    invite_link = context.bot.get_chat(chat.chat_id).link
    if invite_link is None:
        invite_link = context.bot.export_chat_invite_link(chat_id=chat.chat_id)

    chat.update_invite_link(invite_link)
    chat.update_enabled(True)
    update.effective_message.edit_text(
        text=format_chat_settings_message(chat), parse_mode='HTML', reply_markup=generate_chat_settings_markup(chat))


def disable_chat_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('disable_chat_callback chat not founded: {}'.format(chat_id))
        return

    chat.update_enabled(False)
    update.effective_message.edit_text(
        text=format_chat_settings_message(chat), parse_mode='HTML', reply_markup=generate_chat_settings_markup(chat))


def enable_notifications_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('enable_notifications_callback chat not founded: {}'.format(chat_id))
        return

    chat.update_notifications(True)
    run_notification_job(chat=chat, job_queue=context.job_queue, callback=on_notification_callback)

    update.effective_message.edit_text(
        text=format_chat_settings_message(chat), parse_mode='HTML', reply_markup=generate_chat_settings_markup(chat))


def disable_notifications_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('disable_notifications_callback chat not founded: {}'.format(chat_id))
        return

    for job in context.job_queue.get_jobs_by_name(name=chat.title):
        job.schedule_removal()

    chat.update_notifications(False)
    update.effective_message.edit_text(
        text=format_chat_settings_message(chat), parse_mode='HTML', reply_markup=generate_chat_settings_markup(chat))


def change_language_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('change_language_callback chat not founded: {}'.format(chat_id))
        return

    update.effective_message.edit_text(
        text='Choose a language for <b>{chat_title}</b>'.format(chat_title=chat.title),
        reply_markup=generate_languages_markup(chat, settings.LANGUAGES),
        parse_mode='HTML')


def pick_language_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('pick_language_callback chat not founded: {}'.format(chat_id))
        return

    language = context.match.groupdict().get('language_shortcut')
    chat.update_language(language)

    update.effective_message.edit_text(
        text=format_chat_settings_message(chat), reply_markup=generate_chat_settings_markup(chat), parse_mode='HTML')


def change_timezone_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('change_timezone_callback chat not founded: {}'.format(chat_id))
        return

    update.effective_message.edit_text(
        text='Choose a timezone for <b>{chat_title}</b>'.format(chat_title=chat.title),
        reply_markup=generate_timezones_markup(chat, settings.CONFIG['TIMEZONES']),
        parse_mode='HTML')


def pick_timezone_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('pick_timezone_callback chat not founded: {}'.format(chat_id))
        return

    timezone = context.match.groupdict().get('timezone_shortcut')
    chat.update_timezone(timezone)

    update.effective_message.edit_text(
        text=format_chat_settings_message(chat), reply_markup=generate_chat_settings_markup(chat), parse_mode='HTML')


def send_notification_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('send_notification_callback chat not founded: {}'.format(chat_id))
        return

    formatted_chat_statistic = format_chat_stats(
        bot=context.bot, chat=chat, top=settings.GEO_RATING_USERS_COUNT)
    if formatted_chat_statistic is None:
        context.bot.send_message(
            chat_id=chat_id, text=format_chat_notification(chat), reply_markup=generate_start_markup(chat),
            parse_mode='HTML')
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text='{}\n{}'.format(format_chat_notification(chat), formatted_chat_statistic),
            reply_markup=generate_start_markup(chat),
            parse_mode='HTML')

    update.callback_query.answer()


def drop_stats_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('drop_stats_callback chat not founded: {}'.format(chat_id))
        return

    if chat.retrieve_referral_records() is None:
        update.callback_query.answer('Statistic was dropped.')
        return

    with open('awards.json', 'w') as f:
        json.dump(get_user_awards(chat), f)

    update.effective_chat.send_document(open('awards.json', 'rb'))
    context.bot.send_message(
        chat_id=chat.chat_id, text=get_chat_lang(chat).get('contest_end_text'), parse_mode='HTML')
    chat.drop_referral_records()
    update.callback_query.answer('Statistic was dropped.')


def settings_back_callback(update: Update, context: CallbackContext):
    chats = SpectatedChat.get_chats_list()
    update.effective_message.edit_text(text='Choose a chat.', reply_markup=generate_chats_markup(chats))


def generate_ref_link_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    user_id = context.match.groupdict().get('user_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('generate_ref_link_callback chat not founded: {}'.format(chat_id))
        return

    update.effective_chat.send_message(
        text=get_chat_lang(chat).get('referral_link_text').format(
            referral_link=generate_deeplinking_link(chat_id=chat.chat_id, user_id=user_id),
            chat_title=chat.title),
        parse_mode='HTML', disable_web_page_preview=True)
    update.callback_query.answer()


def inline_query_handler(update: Update, context: CallbackContext):
    """
    Handle inline queries.
    Returns a list of spectating channels in which the requesting user is a member.
    """

    bot = context.bot
    query = update.inline_query

    results = []
    for chat in SpectatedChat.get_chats_list(enabled=True):

        if query.query not in chat.title:
            continue

        chat_lang = get_chat_lang(chat)

        # skip if a user is not a member of the chat
        if is_member(bot=bot, chat_id=chat.chat_id, user_id=query.from_user.id) is False:
            continue

        # generate keyboard markup with a referral button
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                text=chat_lang.get('interested_button_text'),
                url=generate_deeplinking_link(chat_id=chat.chat_id, user_id=query.from_user.id))
        ]])

        results.append(InlineQueryResultArticle(
            id=uuid4(),
            title=chat.title,
            reply_markup=markup,
            input_message_content=InputTextMessageContent(
                message_text=chat_lang.get('inline_invite_text').format(chat_title=chat.title),
            parse_mode='HTML')))

    query.answer(results=results, is_personal=True, cache_time=0)


def chat_created_handler(update: Update, context: CallbackContext):
    """Handling group_chat_created and supergroup_chat_created"""

    chat = update.effective_chat

    if has_admin(context.bot, chat.id):
        SpectatedChat.add_to_spectated(chat_id=chat.id, title=chat.title)
        log.info('Add new spectated chat: {}'.format(chat))
        return

    log.info('This chat don\'t have a bot administrator')
    chat.leave()
    return


def new_chat_members_handler(update: Update, context: CallbackContext):
    """Handling new_chat_members messages"""

    bot = context.bot
    message = update.effective_message
    chat = update.effective_chat

    log.info('New new_chat_members message: {}'.format(message))

    if bot.id in [user.id for user in message.new_chat_members]:
        if has_admin(bot, chat.id):
            SpectatedChat.add_to_spectated(chat_id=chat.id, title=chat.title)
            log.info('Add new spectated chat: {}'.format(chat))
        else:
            chat.leave()
            log.info('Leaving the chat: {}'.format(chat))

        return

    if SpectatedChat.is_spectated(chat.id) is False:
        log.info('{} chat is not spectated.')
        chat.leave()
        return

    for user in message.new_chat_members:
        if user.is_bot:
            continue

        record = ReferralRecord.get_by_to_user(chat_id=chat.id, to_user=user.id)
        if record:
            record.update_joined_chat(True)

            cht = SpectatedChat.get_by_chat_id(record.chat_id)
            cht_lang = get_chat_lang(cht)

            context.bot.send_message(
                chat_id=record.to_user_chat_id,
                text=cht_lang.get('join_user_text').format(
                    chat_title=cht.title, invite_button_text=cht_lang.get('invite_button_text')),
                reply_markup=generate_start_markup(chat=cht, user_id=user.id),
                parse_mode='HTML')


def left_chat_member_handler(update: Update, context: CallbackContext):
    """Handling left_chat_member messages"""

    bot = context.bot
    message = update.message
    chat = message.chat

    log.info('New left_chat_member message: {}'.format(message))

    if bot.id == message.left_chat_member.id:
        log.info('Remove spectated chat: {}'.format(chat))
        SpectatedChat.remove_from_spectated(chat_id=chat.id)
        return

    record = ReferralRecord.get_by_to_user(chat_id=chat.id, to_user=message.left_chat_member.id)
    if record:
        record.update_joined_chat(False)


def on_notification_callback(context: CallbackContext):
    chat_id = context.job.context
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('on_notification_callback chat not founded: {}'.format(chat_id))
        return

    log.info('Running update_member_status..')
    update_member_status(bot=context.bot, chat=chat)

    formatted_chat_statistic = format_chat_stats(
        bot=context.bot, chat=chat, top=settings.GEO_RATING_USERS_COUNT)
    if formatted_chat_statistic is None:
        context.bot.send_message(
            chat_id=chat_id, text=format_chat_notification(chat), reply_markup=generate_start_markup(chat),
            parse_mode='HTML')
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text='{}\n{}'.format(format_chat_notification(chat), formatted_chat_statistic),
            reply_markup=generate_start_markup(chat),
            parse_mode='HTML')

