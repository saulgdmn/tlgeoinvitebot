import logging
from functools import wraps

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import yaml

import settings
from database import SpectatedChat, ReferralRecord

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

log = logging.getLogger(__name__)


def get_lang(shortcut):
    for lang in settings.LANGUAGES:
        if lang['shortcut'] == shortcut:
            return lang


def get_chat_lang(chat: SpectatedChat):
    return get_lang(chat.language)


def load_languages_pack(path='./languages.yaml'):

    try:
        with open(path, 'r', encoding='utf8') as f:
            return yaml.load(f)
    except yaml.YAMLError as e:
        log.info('Failed to load {}: {}'.format(path, e))
        return None


def is_admin(bot, chat_id, user_id):
    """Check if user is an administrator"""

    member = bot.get_chat_member(chat_id=chat_id, user_id=user_id)
    if member is None or member.user.id not in settings.ADMINISTRATOR_IDS:
        return False

    return True


def has_admin(bot, chat_id):

    ids = [member.user.id for member in bot.get_chat_administrators(chat_id=chat_id)]
    for id in settings.ADMINISTRATOR_IDS:
        if id in ids:
            return True
    return False


def is_member(bot, chat_id, user_id):
    member = bot.get_chat_member(chat_id=chat_id, user_id=user_id)
    if member is None:
        return False

    return member.status in ['member', 'creator', 'administrator', 'restricted']


def administrators_only(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in settings.ADMINISTRATOR_IDS:
            log.info("Unauthorized access denied for {}.".format(user_id))
            return
        return func(update, context, *args, **kwargs)
    return wrapped


def format_chat_stats(bot, chat: SpectatedChat, top=10):
    """Return a formatted string of user referral statistic"""

    user_stats = chat.retrieve_referral_records()
    if user_stats is None:
        return None

    formatted_users = []
    for key, stat in enumerate(user_stats[:top]):
        user = bot.get_chat_member(chat_id=chat.chat_id, user_id=stat['user_id']).user

        formatted_users.append(
            get_chat_lang(chat).get('user_stat_pattern').format(user_score=stat['invited_users_count'] * settings.GEO_MULT,
                                                                user_mention=user.mention_html()))

    total_invited_users_count = sum([stat['invited_users_count'] for stat in user_stats])
    return get_chat_lang(chat).get('stats_message').format(chat_title=chat.title,
                                                           formatted_users='\n'.join(formatted_users),
                                                           total_invited_users_count=total_invited_users_count)


def format_chat_settings_message(chat: SpectatedChat):
    chat_settings_message_patt = 'Selected <b>{title}</b>:\n\n' \
                                 'Status: <b>{status}</b>\n' \
                                 'Notifications: <b>{notifications}</b>\n' \
                                 'Language: <b>{language}</b>'

    return chat_settings_message_patt.format(title=chat.title,
                                             status='enabled' if chat.enabled else 'disabled',
                                             notifications='enabled' if chat.notifications else 'disabled',
                                             language=chat.language)


def generate_services_markup(chat=None):
    buttons = []

    if chat:
        buttons.append(
            InlineKeyboardButton(text='Try now', url=settings.GEO_WEB_LINK, switch_inline_query=chat.title))
    else:
        buttons.append(
            InlineKeyboardButton(text='Try now', url=settings.GEO_WEB_LINK, switch_inline_query=''))

    buttons.append(InlineKeyboardButton(text='Visit website', url=settings.GEO_WEB_LINK))
    buttons.append(InlineKeyboardButton(text='Download app', url=settings.GEO_APP_LINK))

    return InlineKeyboardMarkup().from_column(buttons)


def generate_chats_markup(chats: [SpectatedChat]):
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton(text=chat.title,
                              callback_data=settings.CALLBACK_DATA_PATTERNS['PICK_CHAT'].
                              format(chat_id=chat.chat_id))
         for chat in chats])


def generate_languages_markup(chat: SpectatedChat, languages: [str]):
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton(text=language['name'],
                              callback_data=settings.CALLBACK_DATA_PATTERNS['PICK_LANGUAGE'].
                              format(chat_id=chat.chat_id,
                                     language_shortcut=language['shortcut']))
         for language in languages])


def generate_chat_settings_markup(chat: SpectatedChat):
    buttons = []

    if chat.enabled:
        buttons.append(
            InlineKeyboardButton(text='Disable chat', callback_data=settings.CALLBACK_DATA_PATTERNS['DISABLE_CHAT'].
                                 format(chat_id=chat.chat_id)))
    else:
        buttons.append(
            InlineKeyboardButton(text='Enable chat', callback_data=settings.CALLBACK_DATA_PATTERNS['ENABLE_CHAT'].
                                 format(chat_id=chat.chat_id)))

    if chat.notifications:
        buttons.append(
            InlineKeyboardButton(text='Disable notifications',
                                 callback_data=settings.CALLBACK_DATA_PATTERNS['DISABLE_NOTIFICATIONS'].
                                 format(chat_id=chat.chat_id)))
    else:
        buttons.append(
            InlineKeyboardButton(text='Enable notifications',
                                 callback_data=settings.CALLBACK_DATA_PATTERNS['ENABLE_NOTIFICATIONS'].
                                 format(chat_id=chat.chat_id)))

    buttons.append(
        InlineKeyboardButton(text='Change a language',
                             callback_data=settings.CALLBACK_DATA_PATTERNS['CHANGE_LANGUAGE'].
                             format(chat_id=chat.chat_id)))

    buttons.append(
        InlineKeyboardButton(text='Send statistic',
                             callback_data=settings.CALLBACK_DATA_PATTERNS['SEND_STATS'].
                             format(chat_id=chat.chat_id)))

    buttons.append(
        InlineKeyboardButton(text='Back to chats',
                             callback_data=settings.CALLBACK_DATA_PATTERNS['SETTINGS_BACK']))

    return InlineKeyboardMarkup.from_column(buttons)
