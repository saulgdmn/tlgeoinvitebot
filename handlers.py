from uuid import uuid4

from telegram import Update
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import InlineQueryResultArticle, InputTextMessageContent

from telegram.ext import Updater, CallbackContext

import settings
from utility import *
from database import SpectatedChat, ReferralRecord


def start_command(update: Update, context: CallbackContext):
    """Handle the command /help issued in private chat."""

    markup = InlineKeyboardMarkup([[InlineKeyboardButton(text='Try now!', switch_inline_query='')]])
    update.effective_chat.send_message(text='start_message', reply_markup=markup, parse_mode='HTML')


@administrators_only
def chats_command_handler(update: Update, context: CallbackContext):
    """Handle the command /chats issued in a private chat."""

    chats = SpectatedChat.get_chats_list()
    log.info(chats)
    if chats is None:
        update.effective_chat.send_message(text='There are no spectated chats!')
        return

    update.effective_chat.send_message(text='Choose a chat.', markup=generate_chats_markup(chats))


def pick_chat_callback(update: Update, context: CallbackContext):

    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('pick_chat_callback chat not founded: {}'.format(chat_id))
        return

    update.effective_message.edit_reply_markup(text=format_chat_settings_message(chat),
                                               markup=generate_chat_settings_markup(chat))


def enable_chat_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('enable_chat_callback chat not founded: {}'.format(chat_id))
        return

    chat.update_enabled(True)
    update.effective_message.edit_reply_markup(text=format_chat_settings_message(chat),
                                               markup=generate_chat_settings_markup(chat))


def disable_chat_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('disable_chat_callback chat not founded: {}'.format(chat_id))
        return

    chat.update_enabled(False)
    update.effective_message.edit_reply_markup(text=format_chat_settings_message(chat),
                                               markup=generate_chat_settings_markup(chat))


def enable_notifications_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('enable_notifications_callback chat not founded: {}'.format(chat_id))
        return

    chat.update_notifications(True)
    update.effective_message.edit_reply_markup(text=format_chat_settings_message(chat),
                                               markup=generate_chat_settings_markup(chat))


def disable_notifications_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('disable_notifications_callback chat not founded: {}'.format(chat_id))
        return

    chat.update_notifications(False)
    update.effective_message.edit_reply_markup(text=format_chat_settings_message(chat),
                                               markup=generate_chat_settings_markup(chat))


def change_language_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('change_language_callback chat not founded: {}'.format(chat_id))
        return

    update.effective_message.edit_reply_markup(text='Choose a language.',
                                               markup=generate_languages_markup(chat, settings.LANGUAGES))


def pick_language_callback(update: Update, context: CallbackContext):

    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('pick_language_callback chat not founded: {}'.format(chat_id))
        return

    language = context.match.groupdict().get('language_shortcut', 'en')
    chat.update_language(language)

    update.effective_message.edit_reply_markup(text=format_chat_settings_message(chat),
                                               markup=generate_chat_settings_markup(chat))


def send_stats_callback(update: Update, context: CallbackContext):
    chat_id = context.match.groupdict().get('chat_id', None)
    chat = SpectatedChat.get_by_chat_id(chat_id)
    if chat is None:
        log.info('send_stats_callback chat not founded: {}'.format(chat_id))
        return

    markup = InlineKeyboardMarkup([[InlineKeyboardButton(text='Try now!', switch_inline_query='')]])
    context.bot.send_message(text=format_chat_stats(context.bot, chat), chat_id=chat_id, reply_markup=markup)


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

        # skip if a user is not a member of the chat
        if is_member(bot=bot, chat_id=chat.chat_id, user_id=query.from_user.id) is False:
            continue

        # create referral button callback data
        # contains 'chat_id' - invited chat_id and 'user_id' - inviting user_id
        callback_data = settings.CALLBACK_DATA_PATTERNS['INVITE_MESSAGE'].\
            format(chat_id=chat.chat_id, user_id=query.from_user.id)

        # generate keyboard markup with a referral button
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(text='Interested!', callback_data=callback_data)]])

        results.append(InlineQueryResultArticle(
            id=uuid4(),
            title=chat.title,
            reply_markup=markup,
            input_message_content=InputTextMessageContent(
                message_text=get_chat_lang(chat).get('invite_message').format(chat_title=chat.title),
                parse_mode='HTML')))

    query.answer(results=results, is_personal=True, cache_time=0)


def invite_message_callback(update: Update, context: CallbackContext):
    """
    Handle the referral button.
    Creates a UserReferralRecord in a database or uses existed.
    """

    log.debug('New callback query: {}'.format(update))

    bot = context.bot
    query = update.callback_query
    invited_chat_id = context.match.groupdict().get('chat_id', None)
    from_user = context.match.groupdict().get('user_id', None)
    to_user = query.from_user.id

    # check if inviting user is an invited user
    if from_user == to_user:
        query.answer(text='You can\'t invite yourself to the chat :)')
        return

    # check if an invited user is already a member of the chat
    if is_member(bot=bot, chat_id=invited_chat_id, user_id=to_user):
        query.answer(text='You\'re already a member of the chat!')
        return

    # check if a user referral record for an invited user is already exists
    # and create if not
    record = ReferralRecord.get(chat_id=invited_chat_id, to_user=to_user)
    if record is None:
        record = ReferralRecord.add(chat_id=invited_chat_id, from_user=from_user, to_user=to_user)

    log.info("Record: {}".format(record.id))

    invited_chat = SpectatedChat.get_by_chat_id(invited_chat_id)

    # generate a new markup with a 'join button'
    new_markup = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(text='Join now!', url=invited_chat.invite_link))

    query.answer(text='Fine! Click the button and join the channel!')
    bot.edit_message_reply_markup(inline_message_id=query.inline_message_id, reply_markup=new_markup)


def chat_created_handler(update: Update, context: CallbackContext):
    """Handling group_chat_created and supergroup_chat_created"""

    chat = update.effective_chat

    if has_admin(context.bot, chat.id):
        SpectatedChat.add_to_spectated(chat_id=chat.id, title=chat.title)
        log.info('Add new spectated chat: {}'.format(chat))
        return

    log.info('This chat don\'t have a bot administrator')
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
            return
        else:
            chat.leave()
            log.info('Leaving the chat: {}'.format(chat))

    if SpectatedChat.is_spectated(chat.id) is False:
        log.info('{} chat is not spectated.')
        return

    for user in message.new_chat_members:
        if user.is_bot:
            continue

        ReferralRecord.get(chat_id=chat.id, to_user=user.id).update_joined_chat(True)


def left_chat_member_handler(update: Update, context: CallbackContext):
    """Handling left_chat_member messages"""

    bot = context.bot
    message = update.message
    chat = message.chat

    log.info('New left_chat_member message: {}'.format(message))

    if bot.id == message.left_chat_member.id:
        log.info('Remove spectated chat: {}'.format(chat))
        SpectatedChat.get_by_chat_id(chat_id=chat.id).remove_from_spectated()
        return

    ReferralRecord.get(chat_id=chat.id, to_user=message.left_chat_member.id).update_joined_chat(False)


def on_notification_callback(context: CallbackContext):

    for chat in SpectatedChat.get_chats_list(enabled=True):
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(text='Try now!', switch_inline_query='')]])
        context.bot.send_message(chat_id=chat.chat_id, text=get_chat_lang(chat).get('notification_message'),
                                 reply_markup=markup, parse_mode='HTML')
