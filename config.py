import os

from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import HttpUrl, IPvAnyAddress, computed_field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.environ.get('ENV_PATH', 'env/stable.env'),
        env_file_encoding='utf-8',
        validate_default=False
    )

    token: str | None = None

    debug: bool = False
    music_only: bool = False

    min_sess_duration: int = 300  # 5 minutes in seconds
    creation_cooldown: int = 15  # seconds

    api_host: IPvAnyAddress = '127.0.0.1'
    api_port: int = 8000

    lavalink_uri: str = 'lavalink'
    lavalink_port: int = 2333
    lavalink_password: str = 'youshallnotpass'

    local_db_engine: MultiHostUrl = 'sqlite+aiosqlite:///'
    local_connection: str = 'local.sqlite3'

    remote_db_engine: MultiHostUrl = 'mysql+asyncmy://'
    remote_connection: str = ''

    defer_sleep_seconds: float = 30

    @computed_field
    def base_uri(self) -> HttpUrl:
        return f'http://{self.api_host}:{self.api_port}'

    @computed_field
    def local_db_uri(self) -> str:
        return f'{self.local_db_engine}{self.local_connection}'

    @computed_field
    def remote_db_uri(self) -> str:
        return f'{self.remote_db_engine}{self.remote_connection}'


Config = Settings()



