import os

import utility

BOT_USERNAME = os.getenv('BOT_USERNAME')
BOT_API_TOKEN = os.getenv('BOT_API_TOKEN')
LANGUAGES_PACK_PATH = os.getenv('LANGUAGES_PACK_PATH')

ADMINISTRATOR_IDS = [401042341, 544498153]

LANGUAGES = utility.load_languages_pack(LANGUAGES_PACK_PATH)

CALLBACK_DATA_PATTERNS = {
    'PICK_CHAT': 'pcht_{chat_id}',

    'ENABLE_CHAT': 'echt_{chat_id}',
    'DISABLE_CHAT': 'dcht_{chat_id}',
    'ENABLE_NOTIFICATIONS': 'entf_{chat_id}',
    'DISABLE_NOTIFICATIONS': 'dntf_{chat_id}',
    'CHANGE_LANGUAGE': 'clng_{chat_id}',
    'SEND_STATS': 'ssts_{chat_id}',
    'SETTINGS_BACK': 'sbck',

    'PICK_LANGUAGE': 'plng_{chat_id}_{language_shortcut}',

    'INVITE_MESSAGE': 'imsg_{chat_id}_{user_id}'
}

CALLBACK_DATA_REGEX = {
    'PICK_CHAT': r'^pcht_(?P<chat_id>[\-\d]+)$',

    'ENABLE_CHAT': r'^echt_(?P<chat_id>[\-\d]+)$',
    'DISABLE_CHAT': r'^dcht_(?P<chat_id>[\-\d]+)$',
    'ENABLE_NOTIFICATIONS': r'^entf_(?P<chat_id>[\-\d]+)$',
    'DISABLE_NOTIFICATIONS': r'^dntf_(?P<chat_id>[\-\d]+)$',
    'CHANGE_LANGUAGE': r'^clng_(?P<chat_id>[\-\d]+)$',
    'SEND_STATS': r'^ssts_(?P<chat_id>[\-\d]+)$',
    'SETTINGS_BACK': r'^sbck$',

    'PICK_LANGUAGE': r'^plng_(?P<chat_id>[\-\d]+)_(?P<language_shortcut>[\-a-z]+)$',

    'INVITE_MESSAGE': r'^imsg_(?P<chat_id>[\-\d]+)_(?P<user_id>[\-\d]+)$'
}