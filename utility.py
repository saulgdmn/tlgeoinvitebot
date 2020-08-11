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


def generate_deeplinking_link(chat_id, user_id):
    return 'https://t.me/{}?start={}'.format(
        settings.BOT_USERNAME,
        settings.CALLBACK_DATA_PATTERNS['DEEPLINKING_LINK'].format(
            chat_id=chat_id, user_id=user_id))


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


def format_chat_stats(bot, chat: SpectatedChat, top):
    """Return a formatted string of user referral statistic"""

    user_stats = chat.retrieve_referral_records()
    if user_stats is None:
        return None

    chat_lang = get_chat_lang(chat)

    formatted_users = []
    for key, stat in enumerate(user_stats[:top]):
        user = bot.get_chat_member(chat_id=chat.chat_id, user_id=stat['user_id']).user

        formatted_users.append(
            chat_lang.get('user_stat_pattern').format(
                user_score=stat['invited_users_count'] * settings.GEO_INVITED_USER_WEIGHT, user_mention=user.mention_html()))

    total_invited_users_count = sum([stat['invited_users_count'] for stat in user_stats])
    return chat_lang.get('statistic_text').format(
        chat_title=chat.title,
        formatted_users='\n'.join(formatted_users),
        total_invited_users_count=total_invited_users_count)


def format_personal_stats(chat: SpectatedChat, user_id):
    invited_users_count = chat.get_personal_referral_records(user_id)
    return get_chat_lang(chat).get('personal_statistic_text').format(
        chat_title=chat.title,
        user_score=invited_users_count * settings.GEO_INVITED_USER_WEIGHT
    )


def format_chat_notification(chat: SpectatedChat):
    return get_chat_lang(chat).get('notification_text').format(
        invite_button_text=get_chat_lang(chat).get('invite_button_text')
    )


def format_chat_settings_message(chat: SpectatedChat):
    chat_settings_message_patt = 'Selected <b>{title}</b>:\n\n' \
                                 'Status: <b>{status}</b>\n' \
                                 'Notifications: <b>{notifications}</b>\n' \
                                 'Language: <b>{language}</b>'

    return chat_settings_message_patt.format(title=chat.title,
                                             status='enabled' if chat.enabled else 'disabled',
                                             notifications='enabled' if chat.notifications else 'disabled',
                                             language=chat.language)


def generate_start_markup(chat=None, user_id=None):
    buttons = []

    if chat:
        lang = get_chat_lang(chat)
    else:
        lang = get_lang('en')

    if chat:
        buttons.append(
            InlineKeyboardButton(text=lang.get('invite_button_text'), switch_inline_query=chat.title))
    else:
        buttons.append(
            InlineKeyboardButton(text=lang.get('invite_button_text'), switch_inline_query=''))

    if chat and user_id:
        buttons.append(
            InlineKeyboardButton(
                text=lang.get('referral_link_button_text'),
                callback_data=settings.CALLBACK_DATA_PATTERNS['GENERATE_REF_LINK'].format(
                    chat_id=chat.chat_id, user_id=user_id)))

    buttons.append(InlineKeyboardButton(text=lang.get('website_button_text'), url=settings.GEO_WEBSITE_LINK))
    buttons.append(InlineKeyboardButton(text=lang.get('app_button_text'), url=settings.GEO_APP_LINK))

    return InlineKeyboardMarkup.from_column(buttons)


def generate_join_markup(chat: SpectatedChat):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text=get_chat_lang(chat).get('join_button_text'),
            url=chat.invite_link)
    ]])


def generate_invite_markup(chat: SpectatedChat = None):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text=get_chat_lang(chat).get('invite_button_text'),
            switch_inline_query='' if chat is None else chat.title)
    ]])


def generate_chats_markup(chats: [SpectatedChat]):
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton(
            text=chat.title,
            callback_data=settings.CALLBACK_DATA_PATTERNS['PICK_CHAT'].format(
                chat_id=chat.chat_id))
         for chat in chats])


def generate_languages_markup(chat: SpectatedChat, languages: [str]):
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton(
            text=language['name'],
            callback_data=settings.CALLBACK_DATA_PATTERNS['PICK_LANGUAGE'].format(
                chat_id=chat.chat_id, language_shortcut=language['shortcut']))
         for language in languages])


def generate_chat_settings_markup(chat: SpectatedChat):
    buttons = []

    if chat.enabled:
        buttons.append(
            InlineKeyboardButton(
                text='Disable chat',
                callback_data=settings.CALLBACK_DATA_PATTERNS['DISABLE_CHAT'].format(
                    chat_id=chat.chat_id)))
    else:
        buttons.append(
            InlineKeyboardButton(
                text='Enable chat',
                callback_data=settings.CALLBACK_DATA_PATTERNS['ENABLE_CHAT'].format(
                    chat_id=chat.chat_id)))

    if chat.notifications:
        buttons.append(
            InlineKeyboardButton(
                text='Disable notifications',
                callback_data=settings.CALLBACK_DATA_PATTERNS['DISABLE_NOTIFICATIONS'].format(
                    chat_id=chat.chat_id)))
    else:
        buttons.append(
            InlineKeyboardButton(
                text='Enable notifications',
                callback_data=settings.CALLBACK_DATA_PATTERNS['ENABLE_NOTIFICATIONS'].format(
                    chat_id=chat.chat_id)))

    buttons.append(
        InlineKeyboardButton(
            text='Change a language',
            callback_data=settings.CALLBACK_DATA_PATTERNS['CHANGE_LANGUAGE'].format(
                chat_id=chat.chat_id)))

    buttons.append(
        InlineKeyboardButton(
            text='Send notification',
            callback_data=settings.CALLBACK_DATA_PATTERNS['SEND_NOTIFICATION'].format(
                chat_id=chat.chat_id)))

    buttons.append(
        InlineKeyboardButton(
            text='Drop statistic',
            callback_data=settings.CALLBACK_DATA_PATTERNS['DROP_STATS'].format(
                chat_id=chat.chat_id)))

    buttons.append(
        InlineKeyboardButton(
            text='\u2190 Back',
            callback_data=settings.CALLBACK_DATA_PATTERNS['SETTINGS_BACK']))

    return InlineKeyboardMarkup.from_column(buttons)
