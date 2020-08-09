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
    'PICK_LANGUAGE': 'plng_{chat_id}_{language_shortcut}',
    'SEND_STATS': 'ssts_{chat_id}',
    'INVITE_MESSAGE': 'imsg_{chat_id}_{user_id}'
}

CALLBACK_DATA_REGEX = {
    'PICK_CHAT': '^pcht_(?<chat_id>[\-\d]+)$',
    'ENABLE_CHAT': '^echt_(?<chat_id>[\-\d]+)$',
    'DISABLE_CHAT': '^dcht_(?<chat_id>[\-\d]+)$',
    'ENABLE_NOTIFICATIONS': '^entf_(?<chat_id>[\-\d]+)$',
    'DISABLE_NOTIFICATIONS': '^dntf_(?<chat_id>[\-\d]+)$',
    'CHANGE_LANGUAGE': '^clng_(?<chat_id>[\-\d]+)$',
    'PICK_LANGUAGE': '^plng_(?<chat_id>[\-\d]+)_(?<language_shortcut>[\-a-z]+)$',
    'SEND_STATS': '^ssts_(?<chat_id>[\-\d]+)$',
    'INVITE_MESSAGE': '^imsg_(?<chat_id>[\-\d]+)_(?<user_id>[\-\d]+)$'
}