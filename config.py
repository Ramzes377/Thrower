from dataclasses import dataclass
from pathlib import Path
from os import getenv, path

import discord
from dotenv import load_dotenv

root = Path(__file__).parent
load_dotenv(path.join(root, getenv('ENV_PATH', 'env/stable.env')))


@dataclass
class Config:
    DEBUG = getenv('DEBUG', 'false').lower() == 'true'
    MUSIC_ONLY = getenv('MUSIC_ONLY', 'false').lower() == 'true'

    TOKEN = getenv('TOKEN')

    GUILD_ID = int(getenv('GUILD_ID'))
    LOGGER_ID = int(getenv('LOGGER_ID'))
    COMMAND_ID = int(getenv('COMMAND_ID'))
    ROLE_REQUEST_ID = int(getenv('ROLE_REQUEST_ID'))
    CREATE_CHANNEL_ID = int(getenv('CREATE_CHANNEL_ID'))
    IDLE_CATEGORY_ID = int(getenv('IDLE_CATEGORY_ID'))
    PLAYING_CATEGORY_ID = int(getenv('PLAYING_CATEGORY_ID'))

    GUILD = discord.Object(id=GUILD_ID)
    DB_ENGINE = getenv('DB_ENGINE', 'sqlite+aiosqlite:///')
    DB_URI = getenv('DB_URI', f'{DB_ENGINE}{root}/local.sqlite3')

    BOT_IDS = list(map(int, getenv('BOT_IDS').split(',')))

    MIN_SESS_DURATION = int(getenv('MIN_SESS_DURATION', 5 * 60))

    LAVALINK_URI = getenv('LAVALINK_URI', '0.0.0.0')
    LAVALINK_PORT = int(getenv('LAVALINK_PORT', '2333'))
    LAVALINK_PASSWORD = getenv('LAVALINK_PASSWORD', 'youshallnotpass')

    API_HOST = getenv('API_HOST', '127.0.0.1')
    API_PORT = int(getenv('API_PORT', '8000'))
    API_VERSION = getenv('API_VERSION', '')

    BASE_URI = f"http://{API_HOST}:{API_PORT}"
