import asyncio
import zoneinfo
import datetime
import discord
import re

from io import BytesIO
from PIL import Image
from PIL.ImageStat import Stat
from hashlib import sha3_224
from itertools import chain
from random import randint

zone_Moscow = zoneinfo.ZoneInfo("Europe/Moscow")

environ = {}
with open('./api/cogs/tools/config.ini') as f:
    for x in f.readlines():
        try:
            k, v = x.split()
            environ[k] = v
        except ValueError:
            pass

create_channel_id = int(environ['create_channel_id'])
logger_id = int(environ['logger_id'])
role_request_id = int(environ['role_request_id'])
command_id = int(environ['command_id'])

bots_ids = [184405311681986560, 721772274830540833]
another_bots_prefixes = (';;', '-v')

categories = {
    discord.ActivityType.playing: int(environ['playing_category']),
    discord.ActivityType.custom: int(environ['idle_category']),
    0: int(environ['idle_category'])
}

database_URL = environ['database_url']
user_data, db_data = database_URL[11:].split('@')
user, password = user_data.split(':')
db_host, db_name = db_data.split('/')
dsn = f'dbname={db_name} user={user} password={password} host={db_host[:-5]}'

token = environ['token']
urls = ['https://youtu.be/gvTsB7GWpTc', 'https://youtu.be/Ii8850-G8S0']

leader_role_rights = discord.PermissionOverwrite(kick_members=True,
                                                 mute_members=False,
                                                 deafen_members=False,
                                                 manage_channels=True,
                                                 create_instant_invite=True)

default_role_rights = discord.PermissionOverwrite(connect=True,
                                                  speak=True,
                                                  use_voice_activation=True,
                                                  kick_members=False,
                                                  mute_members=False,
                                                  deafen_members=False,
                                                  manage_channels=False,
                                                  create_instant_invite=True)


def get_category(user):
    return categories[user.activity.type] if user.activity else categories[0]


def user_is_playing(user):
    return user.activity and user.activity.type == discord.ActivityType.playing


def session_id():
    cur_time = datetime.datetime.now(tz=zone_Moscow)
    start_of_year = datetime.datetime(cur_time.year, 1, 1).astimezone(zone_Moscow)
    n_day_of_year = (cur_time - start_of_year).days + 1
    return n_day_of_year, is_leap_year(cur_time.year)


def get_activity_name(user):  # describe few activities to correct show
    if not user.activity or user.activity.type == discord.ActivityType.custom:
        return f"{user.display_name}'s channel"
    return f"[{re.compile('[^a-zA-Z0-9а-яА-Я +]').sub('', user.activity.name)}]"


def get_app_id(activity_interval):
    try:
        app_id, is_real = activity_interval.activity.application_id, True
    except AttributeError:
        app_id, is_real = _hash(activity_interval.activity.name), False
    return app_id, is_real


def get_cur_user_channel(user):
    return None if not user.voice else user.voice.channel


async def edit_channel_name_category(user, channel, overwrites=None):
    channel_name = get_activity_name(user)
    category = get_category(user)
    try:
        await asyncio.wait_for(channel.edit(name=channel_name, category=category, overwrites=overwrites), timeout=5.0)
    except asyncio.TimeoutError:  # Trying to rename channel in transfer but Discord restrictions :('
        await channel.edit(category=category)


def time_format(time):
    return "%02d:%02d:%02d - %02d.%02d.%04d" % (time.hour, time.minute, time.second, time.day, time.month, time.year)


def _hash(string):
    return int(str(sha3_224(string.encode(encoding='utf8')).hexdigest()), 16) % 10 ** 10


def is_leap_year(year):
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    if year % 4 == 0:
        return True
    return False


def get_pseudo_random_color():
    return randint(70, 255), randint(70, 255), randint(70, 255)


def flatten(collection):
    return chain(*collection) if collection is not None else []


def get_mean_color(raw_img):
    return [int(x) for x in Stat(Image.open(BytesIO(raw_img))).mean[:3]]


def get_dominant_colors(raw_img, numcolors=5, resize=64):
    img = Image.open(BytesIO(raw_img))
    img = img.copy()
    img.thumbnail((resize, resize))
    paletted = img.convert('P', palette=Image.Palette.ADAPTIVE, colors=numcolors)
    palette = paletted.getpalette()
    color_counts = sorted(paletted.getcolors(), reverse=True)
    colors = []
    for i in range(numcolors):
        palette_index = color_counts[i][1]
        dominant_color = dc = tuple(palette[palette_index*3:palette_index*3+3])
        sq_dist = dc[0]*dc[0] + dc[1]*dc[1] + dc[2]*dc[2]
        if sq_dist > 8:  # drop too dark colors
            colors.append(dominant_color)
    return colors
