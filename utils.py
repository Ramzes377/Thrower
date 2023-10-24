import asyncio
import logging
import warnings
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Type

import discord
import fastapi
from httpx import AsyncClient

from config import Config

offset = timedelta(hours=3)
tzMoscow = timezone(offset, name='МСК')


def now() -> datetime:
    return datetime.now(tz=tzMoscow).replace(microsecond=0, tzinfo=None)


logger = logging.getLogger('discord.client')


async def clear_messages(bot: discord.Client, guild_id: int):
    guild = bot.get_guild(guild_id)
    text_channels = [channel for channel in guild.channels if
                     channel.type.name == 'text']
    messages = await request('sent_message')
    for message in messages:
        for channel in text_channels:
            with suppress(discord.NotFound):
                if msg := await channel.fetch_message(message['id']):
                    logger.info(msg)
                    # deletion process
                    # await msg.delete()
                else:
                    logger.warning(
                        await request(f'sent_message/{msg.id}', 'delete')
                    )


async def request(
        url: str,
        method: str = 'get',
        data: dict | None = None,
        params: dict | None = None,
        base_url: str = Config.BASE_URI,
) -> dict | list[dict]:
    from api.base import app

    async with AsyncClient(app=app, base_url=base_url) as client:
        if method in ('get', 'delete'):
            response = await client.request(method, url, params=params)
        else:
            data = fastapi.encoders.jsonable_encoder(data)  # noqa
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


class CustomWarning(Warning):
    default_format = warnings.formatwarning

    @classmethod
    def formatwarning(
            cls: Type['CustomWarning'],
            msg: str,
            category: Type[Warning],
            filename: str,
            lineno: int,
            *args,
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


async def _fill_activity_info():
    all_activities = await request('activity_info')

    url = 'https://discord.com/api/v10/applications/detectable'

    async with AsyncClient() as client:
        response = await client.request('get', url)
        data = response.json()

    coroutines = []
    for x in data:
        if icon := x.get('icon', x.get('cover_image')):
            app_id, app_name = int(x['id']), x['name']
            icon_url = f'https://cdn.discordapp.com/app-icons/{app_id}/{icon}.png?size=4096'
            game_data = {'icon_url': icon_url, 'app_id': app_id,
                         'app_name': app_name}
            coroutines.append(request('activity_info', 'post', data=game_data))

    if len(all_activities) != len(coroutines):
        await asyncio.gather(*coroutines)
