import json
import os

from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, DotEnvSettingsSource
from pydantic import HttpUrl, IPvAnyAddress

import discord


class CustomSources(DotEnvSettingsSource):
    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value, is_complex: bool
    ):
        if field_name == 'BOT_IDS':
            return json.loads(f'[{value}]')
        return super().prepare_field_value(field_name, field, value, is_complex)


class Settings(BaseSettings):

    @classmethod
    def settings_customise_sources(
        cls, settings_cls, **kw
    ):
        env_file = kw['dotenv_settings'].env_file
        return CustomSources(settings_cls=settings_cls, env_file=env_file),

    DEBUG: bool

    TOKEN: str
    GUILD_ID: int
    LOGGER_ID: int
    COMMAND_ID: int
    ROLE_REQUEST_ID: int
    CREATE_CHANNEL_ID: int
    IDLE_CATEGORY_ID: int
    PLAYING_CATEGORY_ID: int
    BOT_IDS: list[int]

    MUSIC_ONLY: bool
    MIN_SESS_DURATION: int = 300  # 5 minutes in seconds

    API_HOST: IPvAnyAddress = '127.0.0.1'
    API_PORT: int = 8000

    DB_ENGINE: str = 'sqlite+aiosqlite:///'

    LAVALINK_URI: str = 'lavalink'
    LAVALINK_PORT: int = 2333
    LAVALINK_PASSWORD: str = 'youshallnotpass'

    GUILD: discord.Object | None = None
    DB_URI: str | None = None
    BASE_URI: HttpUrl | None = None


Config = Settings(
    _env_file=os.environ.get('ENV_PATH', 'env/stable.env'),
    _env_file_encoding='utf-8'
)

Config.GUILD = discord.Object(id=Config.GUILD_ID)
Config.BASE_URI = f'http://{Config.API_HOST}:{Config.API_PORT}'
Config.DB_URI = f'{Config.DB_ENGINE}./local.sqlite3'

