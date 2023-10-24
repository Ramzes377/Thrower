import os

from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import HttpUrl, IPvAnyAddress


class Settings(BaseSettings):
    model_config = SettingsConfigDict(validate_default=False)

    TOKEN: str | None = None

    DEBUG: bool = False
    MUSIC_ONLY: bool = False

    MIN_SESS_DURATION: int = 300  # 5 minutes in seconds
    CREATION_COOLDOWN: int = 15  # seconds

    API_HOST: IPvAnyAddress = '127.0.0.1'
    API_PORT: int = 8000
    BASE_URI: HttpUrl = f'http://{API_HOST}:{API_PORT}'

    LAVALINK_URI: str = 'lavalink'
    LAVALINK_PORT: int = 2333
    LAVALINK_PASSWORD: str = 'youshallnotpass'

    DB_ENGINE: MultiHostUrl = 'sqlite+aiosqlite:///'
    DB_URI: MultiHostUrl = f'{DB_ENGINE}./local.sqlite3'


Config = Settings(
    _env_file=os.environ.get('ENV_PATH', 'env/stable.env'),
    _env_file_encoding='utf-8'
)
