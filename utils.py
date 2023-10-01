import logging
import warnings
from contextlib import suppress
from datetime import datetime, timedelta, timezone

import discord
from config import Config

offset = timedelta(hours=3)
tzMoscow = timezone(offset, name='МСК')


def now() -> datetime:
    return datetime.now(tz=tzMoscow).replace(microsecond=0,
                                                      tzinfo=None)


logger = logging.getLogger('discord.client')


async def clear_messages(bot):
    from api.base import request

    if Config.GUILD_ID is None:
        return

    guild = bot.get_guild(Config.GUILD_ID)
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
