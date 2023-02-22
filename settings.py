from zoneinfo import ZoneInfo

import discord
from envparse import Env

tzMoscow = ZoneInfo("Europe/Moscow")

DEBUG = False

env = Env()
if DEBUG:
    env.read_envfile('.env-test')
else:
    env.read_envfile()

env_vars_names = ['guild_id', 'logger_id', 'command_id',
                  'role_request_id', 'create_channel_id',
                  'idle_category_id', 'playing_category_id']

envs = {var: env(var, cast=int) for var in env_vars_names}

token = env.str('token')
guild = discord.Object(id=envs['guild_id'])
database_URL = env.str('database_url', default='sqlite:///local.sqlite3')
bots_ids = [int(bot_id) for bot_id in env.list('bots_ids')]
