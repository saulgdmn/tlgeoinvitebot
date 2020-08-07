
from telegram import Update
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

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

    chats = SpectatedChat.get_list()
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

