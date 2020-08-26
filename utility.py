import logging
import datetime
import re
from functools import wraps
import html
import json
import traceback
import math

import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import JobQueue, CallbackContext

import yaml
import reverse_geocode

import settings
from database import SpectatedChat

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

log = logging.getLogger(__name__)


def get_lang(shortcut):
    for lang in settings.LANGUAGES:
        if lang['shortcut'] == shortcut:
            return lang


def get_tmzn(shortcut):
    for tmzn in settings.CONFIG['TIMEZONES']:
        if tmzn['shortcut'] == shortcut:
            return tmzn


def get_chat_lang(chat: SpectatedChat):
    return get_lang(chat.language)


def get_chat_tmzn(chat: SpectatedChat):
    return get_tmzn(chat.timezone)


def load_config(path):
    try:
        with open(path, 'r', encoding='utf8') as f:
            return yaml.load(f)
    except yaml.YAMLError as e:
        log.info('Failed to load {}: {}'.format(path, e))
        return None


def load_languages(path):
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


def verify_location(long, lat, chat: SpectatedChat):
    loc = reverse_geocode.get((lat, long))
    log.info(loc)
    return loc.get('country_code') == get_chat_lang(chat).get('country_code')


def administrators_only(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in settings.ADMINISTRATOR_IDS:
            log.info("Unauthorized access denied for {}.".format(user_id))
            return
        return func(update, context, *args, **kwargs)
    return wrapped


def run_notification_job(chat: SpectatedChat, job_queue: JobQueue, callback):
    for h in range(settings.NOTIFICATION_START_TIME, settings.NOTIFICATION_END_TIME, 1):
        tmzn = get_chat_tmzn(chat)

        m = re.match(
            pattern=r'^(?P<div>\-|\+)(?P<h>[\d]{2}):(?P<m>[\d]{2})$', string=tmzn['offset'])
        if m is None:
            log.info('run_notification_job failed: wrong timezone[offset]')
            return

        if m.groupdict()['div'] == '+':
            offset = datetime.timedelta(hours=int(m.groupdict()['h']), minutes=int(m.groupdict()['m']))
        else:
            offset = -datetime.timedelta(hours=int(m.groupdict()['h']), minutes=int(m.groupdict()['m']))

        j = job_queue.run_daily(
            name=chat.title, callback=callback, time=datetime.time(hour=h, tzinfo=datetime.timezone(offset=offset)),
            context=chat.chat_id)


def update_member_status(bot, chat: SpectatedChat):
    for r in chat.retrieve_invited_users_referral_records():
        try:
            member = bot.get_chat_member(chat_id=chat.chat_id, user_id=r.to_user)
        except telegram.error.BadRequest:
            r.update_joined_chat(False)
            log.info('Updating status for a member: {} '.format(member))
            continue

        if member is None or member.user is None or member.status in ['kicked', 'left']:
            r.update_joined_chat(False)
            log.info('Updating status for a member: {} '.format(member))
            continue

        #r.update_joined_chat(True)


def setup_notification_jobs(job_queue: JobQueue, callback):

    for chat in SpectatedChat.get_chats_list(enabled=True):
        run_notification_job(chat=chat, job_queue=job_queue, callback=callback)


def get_user_awards(chat: SpectatedChat, bot):

    results = []

    for c in chat.retrieve_referral_records():
        try:
            user = bot.get_chat_member(chat_id=chat.chat_id, user_id=c['user_id']).user
        except Exception as e:
            log.error(e)
            continue

        results.append({
            'user_id': c['user_id'],
            'award': c['invited_users_count'] * settings.GEO_INVITED_USER_WEIGHT,
            'username': user.username,
            'full_name': user.full_name
        })

    return results


def generate_deeplinking_link(chat_id, user_id):
    return 'https://t.me/{}?start={}'.format(
        settings.BOT_USERNAME,
        settings.CALLBACK_DATA_PATTERNS['DEEPLINKING_LINK'].format(
            chat_id=chat_id, user_id=user_id))


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
                invited_users_count=stat['invited_users_count'],
                user_score=stat['invited_users_count'] * settings.GEO_INVITED_USER_WEIGHT,
                user_mention=user.mention_html()))

    total_invited_users_count = sum([stat['invited_users_count'] for stat in user_stats])
    return chat_lang.get('statistic_text').format(
        chat_title=chat.title,
        formatted_users='\n'.join(formatted_users),
        total_invited_users_count=total_invited_users_count)


def format_invite_contest_texts(bot, chat: SpectatedChat):
    """Return a formatted string of user referral statistic"""

    user_stats = chat.retrieve_referral_records()
    if user_stats is None:
        return None

    chat_lang = get_chat_lang(chat)

    formatted_users = []
    for key, stat in enumerate(user_stats):
        user = bot.get_chat_member(chat_id=chat.chat_id, user_id=stat['user_id']).user

        formatted_users.append(
            chat_lang.get('user_stat_pattern').format(
                invited_users_count=stat['invited_users_count'],
                user_score=stat['invited_users_count'] * settings.GEO_INVITED_USER_WEIGHT,
                user_mention=user.mention_html()))

    return ['\n'.join(formatted_users[i*40:(i+1)*40]) for i in range(math.ceil(len(formatted_users)/40))]


def format_personal_stats(chat: SpectatedChat, user_id):
    invited_users_count = chat.retrieve_personal_referral_records(user_id)
    return get_chat_lang(chat).get('personal_statistic_text').format(
        chat_title=chat.title,
        invited_users_count=invited_users_count,
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
                                 'Language: <b>{language}</b>\n' \
                                 'Timezone: <b>{timezone}</b>'

    return chat_settings_message_patt.format(title=chat.title,
                                             status='enabled' if chat.enabled else 'disabled',
                                             notifications='enabled' if chat.notifications else 'disabled',
                                             language=get_chat_lang(chat).get('name'),
                                             timezone=get_chat_tmzn(chat).get('name'))


def format_error_message(update: Update, context: CallbackContext):
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb = ''.join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    text = (
        'An exception was raised while handling an update\n'
        '<pre>update = {}</pre>\n\n'
        '<pre>context.chat_data = {}</pre>\n\n'
        '<pre>context.user_data = {}</pre>\n\n'
        '<pre>context.job = {}</pre>\n\n'
        '<pre>context.matches = {}</pre>\n\n'
        '<pre>{}</pre>'
    ).format(
        html.escape('' if update is None else json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(str(context.chat_data)),
        html.escape(str(context.user_data)),
        html.escape(str(context.job)),
        html.escape(str(context.matches)),
        html.escape(tb)
    )

    return text


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


def generate_request_location_markup(chat: SpectatedChat):
    return ReplyKeyboardMarkup(
            keyboard=[[
                KeyboardButton(
                    text=get_chat_lang(chat).get('request_location_button_text'), request_location=True),
                KeyboardButton(
                    text=get_chat_lang(chat).get('request_location_cancel_button_text')
                )]],
            one_time_keyboard=False, resize_keyboard=True)


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


def generate_timezones_markup(chat: SpectatedChat, timezones):
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton(
            text=timezone['name'],
            callback_data=settings.CALLBACK_DATA_PATTERNS['PICK_TIMEZONE'].format(
                chat_id=chat.chat_id, timezone_shortcut=timezone['shortcut']))
         for timezone in timezones])


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
            text='Change a timezone',
            callback_data=settings.CALLBACK_DATA_PATTERNS['CHANGE_TIMEZONE'].format(
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
