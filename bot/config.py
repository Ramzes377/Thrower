from dataclasses import dataclass
from os import getenv

import discord
from dotenv import load_dotenv

load_dotenv(getenv('ENV_PATH', './env/stable.env'))


@dataclass
class Config:
    DEBUG = getenv('DEBUG', 'False') == 'True'
    MUSIC_ONLY = getenv('MUSIC_ONLY', 'False') == 'True'

    TOKEN = getenv('TOKEN')

    GUILD_ID = int(getenv('GUILD_ID'))
    LOGGER_ID = int(getenv('LOGGER_ID'))
    COMMAND_ID = int(getenv('COMMAND_ID'))
    ROLE_REQUEST_ID = int(getenv('ROLE_REQUEST_ID'))
    CREATE_CHANNEL_ID = int(getenv('CREATE_CHANNEL_ID'))
    IDLE_CATEGORY_ID = int(getenv('IDLE_CATEGORY_ID'))
    PLAYING_CATEGORY_ID = int(getenv('PLAYING_CATEGORY_ID'))

    GUILD = discord.Object(id=GUILD_ID)
    DB_URI = getenv('DB_URI', 'sqlite:///local.sqlite3')

    BOT_IDS = list(map(int, getenv('BOT_IDS').split(',')))

    MIN_SESS_DURATION = int(getenv('MIN_SESS_DURATION', 5 * 60))
