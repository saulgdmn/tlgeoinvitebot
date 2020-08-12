import os

from utility import load_config, load_languages

CONFIG = load_config(os.getenv('CONFIG_PATH'))
LANGUAGES = load_languages(os.getenv('LANGUAGES_PATH'))

BOT_USERNAME = CONFIG['BOT_USERNAME']
BOT_API_TOKEN = CONFIG['BOT_API_TOKEN']

GEO_WEBSITE_LINK = CONFIG['GEO_WEBSITE_LINK']
GEO_APP_LINK = CONFIG['GEO_APP_LINK']

GEO_INVITED_USER_WEIGHT = CONFIG['GEO_INVITED_USER_WEIGHT']
GEO_RATING_USERS_COUNT = CONFIG['GEO_RATING_USERS_COUNT']

NOTIFICATION_START_TIME = CONFIG['NOTIFICATION_START_TIME']
NOTIFICATION_END_TIME = CONFIG['NOTIFICATION_END_TIME']

ADMINISTRATOR_IDS = [401042341, 544498153]

VERIFY_LOCATION_CONV_ID = 1

CALLBACK_DATA_PATTERNS = {
    'PICK_CHAT': 'pcht_{chat_id}',

    'ENABLE_CHAT': 'echt_{chat_id}',
    'DISABLE_CHAT': 'dcht_{chat_id}',
    'ENABLE_NOTIFICATIONS': 'entf_{chat_id}',
    'DISABLE_NOTIFICATIONS': 'dntf_{chat_id}',
    'CHANGE_LANGUAGE': 'clng_{chat_id}',
    'CHANGE_TIMEZONE': 'ctmz_{chat_id}',
    'SEND_NOTIFICATION': 'sntf_{chat_id}',
    'DROP_STATS': 'dsts_{chat_id}',
    'SETTINGS_BACK': 'sbck',

    'PICK_LANGUAGE': 'plng_{chat_id}_{language_shortcut}',
    'PICK_TIMEZONE': 'ptmz_{chat_id}_{timezone_shortcut}',

    'DEEPLINKING_LINK': 'dlnk_{chat_id}_{user_id}',
    'GENERATE_REF_LINK': 'rlnk_{chat_id}_{user_id}',
}

CALLBACK_DATA_REGEX = {
    'PICK_CHAT': r'^pcht_(?P<chat_id>[\-\d]+)$',

    'ENABLE_CHAT': r'^echt_(?P<chat_id>[\-\d]+)$',
    'DISABLE_CHAT': r'^dcht_(?P<chat_id>[\-\d]+)$',
    'ENABLE_NOTIFICATIONS': r'^entf_(?P<chat_id>[\-\d]+)$',
    'DISABLE_NOTIFICATIONS': r'^dntf_(?P<chat_id>[\-\d]+)$',
    'CHANGE_LANGUAGE': r'^clng_(?P<chat_id>[\-\d]+)$',
    'CHANGE_TIMEZONE': r'^ctmz_(?P<chat_id>[\-\d]+)$',
    'SEND_NOTIFICATION': r'^sntf_(?P<chat_id>[\-\d]+)$',
    'DROP_STATS': r'^dsts_(?P<chat_id>[\-\d]+)$',
    'SETTINGS_BACK': r'^sbck$',

    'PICK_LANGUAGE': r'^plng_(?P<chat_id>[\-\d]+)_(?P<language_shortcut>[\-a-z]+)$',
    'PICK_TIMEZONE': r'^ptmz_(?P<chat_id>[\-\d]+)_(?P<timezone_shortcut>[\-a-z]+)$',

    'DEEPLINKING_LINK': r'^\/start dlnk_(?P<chat_id>[\-\d]+)_(?P<user_id>[\-\d]+)$',
    'GENERATE_REF_LINK': r'^rlnk_(?P<chat_id>[\-\d]+)_(?P<user_id>[\-\d]+)$',
}