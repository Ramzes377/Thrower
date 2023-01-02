import datetime
from io import BytesIO
from hashlib import sha3_224
from random import randint

import discord

from PIL import Image

from api.bot.vars import categories, tzMoscow


def get_category(user: discord.Member) -> discord.CategoryChannel:
    return categories[user.activity.type] if user.activity else categories[0]


def get_voice_channel(user: discord.Member):
    return user.voice.channel if user.voice else None


def user_is_playing(user: discord.Member) -> bool:
    return user.activity and user.activity.type == discord.ActivityType.playing


def get_app_id(user: discord.Member) -> tuple[int, bool]:
    try:
        app_id, is_real = user.activity.application_id, True
    except AttributeError:
        try:
            app_id, is_real = _hash(user.activity.name), False
        except AttributeError:
            app_id, is_real = None, False
    return app_id, is_real


def fmt(dt: datetime.datetime) -> str:
    return dt.strftime('%H:%M %d/%m')


def dt_from_str(s: str) -> datetime.datetime:
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')


def _hash(string: str) -> int:
    return int(str(sha3_224(string.encode(encoding='utf8')).hexdigest()), 16) % 10 ** 10


def get_pseudo_random_color() -> tuple[int, int, int]:
    return randint(70, 255), randint(70, 255), randint(70, 255)


def get_dominant_color(raw_img, numcolors=5, resize=64) -> tuple[int, int, int] | list:
    img = Image.open(BytesIO(raw_img))
    img = img.copy()
    img.thumbnail((resize, resize))
    paletted = img.convert('P', palette=Image.Palette.ADAPTIVE, colors=numcolors)
    palette = paletted.getpalette()
    color_counts = sorted(paletted.getcolors(), reverse=True)
    colors = []
    for i in range(numcolors):
        palette_index = color_counts[i][1]
        dominant_color = dc = tuple(palette[palette_index * 3:palette_index * 3 + 3])
        sq_dist = dc[0] * dc[0] + dc[1] * dc[1] + dc[2] * dc[2]
        if sq_dist > 8:  # drop too dark colors
            colors.append(dominant_color)
    return colors[0]


def now() -> datetime.datetime:
    return datetime.datetime.now(tz=tzMoscow)


def code_block(func):
    def wrapper(*args, **kwargs) -> str:
        wrap = '```'
        result = func(*args, **kwargs)
        return f'{wrap}{result}{wrap}'
    return wrapper
