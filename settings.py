import datetime
import logging
import warnings
from contextlib import suppress
from dataclasses import dataclass

import discord
from envparse import Env


offset = datetime.timedelta(hours=3)
tzMoscow = datetime.timezone(offset, name='МСК')


def now() -> datetime:
    return datetime.datetime.now(tz=tzMoscow).replace(microsecond=0, tzinfo=None)


MUSIC_ONLY = True
DEBUG = False

env = Env()
env_file = '.env-test' if DEBUG else None
env.read_envfile(env_file)

env_vars_names = [
    'guild_id',
    'logger_id',
    'command_id',
    'role_request_id',
    'create_channel_id',
    'idle_category_id',
    'playing_category_id'
]

envs = {var: env(var, cast=int) for var in env_vars_names}

token = env.str('token')
guild = discord.Object(id=envs['guild_id'])
database_URL = env.str('database_url', default='sqlite:///local.sqlite3')
bots_ids = [int(bot_id) for bot_id in env.list('bots_ids')]


@dataclass(frozen=True)
class Permissions:
    default = discord.PermissionOverwrite(
        kick_members=False,
        manage_channels=False,
        create_instant_invite=True
    )
    leader = discord.PermissionOverwrite(
        kick_members=True,
        manage_channels=True,
        create_instant_invite=True
    )


def _init_channels(bot: discord.Client) -> dataclass:
    @dataclass(frozen=True)
    class Channels:
        create: discord.VoiceChannel = bot.get_channel(envs['create_channel_id'])
        logger: discord.VoiceChannel = bot.get_channel(envs['logger_id'])
        request: discord.VoiceChannel = bot.get_channel(envs['role_request_id'])
        commands: discord.VoiceChannel = bot.get_channel(envs['command_id'])

    return Channels


def _init_categories(bot: discord.Client) -> dict:
    return {
        None: bot.get_channel(envs['idle_category_id']),
        discord.ActivityType.playing: bot.get_channel(envs['playing_category_id'])
    }


logger = logging.getLogger('discord.client')


async def clear_unregistered_messages(bot):
    from api.rest.base import request
    guild = bot.get_guild(envs['guild_id'])
    text_channels = [channel for channel in guild.channels if channel.type.name == 'text']
    messages = await request('sent_message/')
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


class CustomWarning(Warning):
    default_format = warnings.formatwarning

    @classmethod
    def formatwarning(
            cls: 'CustomWarning',
            msg: str,
            category: Warning,
            filename: str,
            lineno: int,
            file: str = None,
            line: int = None,
            **kwargs
    ):
        if issubclass(category, cls):
            return f'{filename}: {lineno}: {msg}\n'

        return cls.default_format(msg, category, filename, lineno, **kwargs)


warnings.formatwarning = CustomWarning.formatwarning
