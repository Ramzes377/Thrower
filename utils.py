import asyncio
import logging
import warnings
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from logging.handlers import RotatingFileHandler
from typing import Callable, Type

import discord
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient

from config import Config

offset = timedelta(hours=3)
tzMoscow = timezone(offset, name='МСК')

NotFoundException = HTTPException(status_code=404, detail='Not found!')


class CrudType(Enum):
    CR = 'CR'
    CRU = 'CRU'
    CRUD = 'CRUD'


def now() -> datetime:
    return datetime.now(tz=tzMoscow).replace(microsecond=0, tzinfo=None)


def table_to_json(table) -> dict:
    return jsonable_encoder(table.__dict__, exclude={'_sa_instance_state'})


def _init_loggers() -> tuple[logging.Logger, logging.Logger]:
    class _ColourFormatter(logging.Formatter):
        """ Taken from discord api to uniform logging. """

        LEVEL_COLOURS = [
            (logging.DEBUG, '\x1b[40;1m'),
            (logging.INFO, '\x1b[34;1m'),
            (logging.WARNING, '\x1b[33;1m'),
            (logging.ERROR, '\x1b[31m'),
            (logging.CRITICAL, '\x1b[41m'),
        ]

        FORMATS = {
            level: logging.Formatter(
                f'\x1b[30;1m%(asctime)s\x1b[0m {colour}%(levelname)-8s\x1b[0m \x1b[35m%(name)s\x1b[0m %(message)s',
                '%Y-%m-%d %H:%M:%S',
            )
            for level, colour in LEVEL_COLOURS
        }

        def format(self, record):
            formatter = self.FORMATS.get(record.levelno)
            if formatter is None:
                formatter = self.FORMATS[logging.DEBUG]

            # Override the traceback to always print in red
            if record.exc_info:
                text = formatter.formatException(record.exc_info)
                record.exc_text = f'\x1b[31m{text}\x1b[0m'

            output = formatter.format(record)

            # Remove the cache layer
            record.exc_text = None
            return output

    level = logging.DEBUG if Config.debug else logging.ERROR

    _logger = logging.getLogger(name="thrower.api")
    _logger.setLevel(logging.DEBUG)

    strerr_handler = logging.StreamHandler()
    strerr_handler.setFormatter(_ColourFormatter())
    strerr_handler.setLevel(level=level)

    file_handler = RotatingFileHandler('log.log', encoding='utf-8')
    file_handler.setFormatter(
        logging.Formatter(
            fmt='[%(asctime)s] [%(levelname)s    ] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
    )
    file_handler.setLevel(logging.DEBUG)

    _discord_log = logging.getLogger('discord.client')
    _discord_log.setLevel(level=level)

    _logger.addHandler(file_handler)
    _logger.addHandler(strerr_handler)

    return _logger, _discord_log


logger, discord_logger = _init_loggers()


async def clear_messages(bot: discord.Client, guild_id: int):
    guild = bot.get_guild(guild_id)
    text_channels = [channel for channel in guild.channels if
                     channel.type.name == 'text']
    messages = await request('sent_message')
    for message in messages:
        for channel in text_channels:
            with suppress(discord.NotFound):
                if msg := await channel.fetch_message(message['id']):
                    discord_logger.debug(msg)
                    # deletion process
                    # await msg.delete()
                else:
                    discord_logger.warning(
                        await request(f'sent_message/{msg.id}', 'delete')
                    )


async def request(
        url: str,
        method: str = 'get',
        data: dict | None = None,
        params: dict | None = None,
        base_url: str = Config.base_uri,
) -> dict | list[dict]:
    from api.base import app

    async with AsyncClient(app=app, base_url=base_url) as client:
        if method in ('get', 'delete'):
            response = await client.request(method, url, params=params)
        else:
            data = jsonable_encoder(data)  # noqa
            response = await client.request(
                method,
                url,
                params=params,
                json=data
            )

    return response.json()


async def guild_channels() -> dict[int, dict]:
    items = await request('guild')
    as_dict = {item.pop('id'): item['initialized_channels'] for item in items}
    return as_dict


def handle_dict(
        d: dict,
        key_handler: Callable = lambda x: x,
        value_handler: Callable = lambda x: x,
) -> dict:
    return {key_handler(k): value_handler(v) for k, v in d.items()}


def format_dict(dct: dict) -> str:
    return ', '.join(f'{k} = {v}' for k, v in dct.items())


class CustomWarning(Warning):
    default_format = warnings.formatwarning

    @classmethod
    def formatwarning(
            cls: Type['CustomWarning'],
            msg: str,
            category: Type[Warning],
            filename: str,
            lineno: int,
            *args,  # noqa
            **kwargs
    ):
        if issubclass(category, cls):
            return f'{filename}: {lineno}: {msg}\n'

        return cls.default_format(msg, category, filename, lineno, **kwargs)


warnings.formatwarning = CustomWarning.formatwarning


@dataclass(frozen=True)
class GuildChannels:
    create: discord.VoiceChannel
    logger: discord.VoiceChannel
    role_request: discord.VoiceChannel
    commands: discord.VoiceChannel
    playing_category: discord.CategoryChannel
    idle_category: discord.CategoryChannel


async def _init_channels(bot: discord.Client) -> dict[int, dataclass]:
    def to_dataclass(ids: dict):
        return GuildChannels(**handle_dict(ids, value_handler=bot.get_channel))

    db_channels = await guild_channels()
    channels = handle_dict(db_channels, value_handler=to_dataclass)

    return channels


async def create_if_not_exists(
        get_url: str,
        post_url: str,
        object_: dict
) -> dict | None:
    data = await request(url=get_url)
    if 'detail' not in data:
        return

    return await request(post_url, 'post', data=object_)


async def _fill_activity_info():
    all_activities = await request('activity_info')
    activity_ids = {row['app_id'] for row in all_activities}

    url = 'https://discord.com/api/v10/applications/detectable'

    async with AsyncClient() as client:
        response = await client.request('get', url)
        data = response.json()

    coroutines = []
    for x in data:
        if not (icon := x.get('icon', x.get('cover_image'))):
            continue

        app_id, app_name = int(x['id']), x['name']

        if app_id in activity_ids:
            continue

        icon_url = f'https://cdn.discordapp.com/app-icons/{app_id}/{icon}.png?size=4096'
        game_data = {'icon_url': icon_url, 'app_id': app_id,
                     'app_name': app_name}

        coroutines.append(
            create_if_not_exists(
                get_url=f'activity_info/{app_id}',
                post_url='activity_info',
                object_=game_data
            )
        )

    await asyncio.gather(*coroutines)
