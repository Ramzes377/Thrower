import discord
from zoneinfo import ZoneInfo

tzMoscow = ZoneInfo("Europe/Moscow")

with open('env') as f:
    environ = dict(x.split() for x in f.readlines() if x != '\n')

guild_id = int(environ['guild_id'])
create_channel_id = int(environ['create_channel_id'])
logger_id = int(environ['logger_id'])
role_request_id = int(environ['role_request_id'])
command_id = int(environ['command_id'])

categories = {
    discord.ActivityType.playing: int(environ['playing_category']),
    discord.ActivityType.custom: int(environ['idle_category']),
    0: int(environ['idle_category'])
}

bots_ids = [184405311681986560, 721772274830540833]
another_bots_prefixes = ('/',)

database_URL = environ['database_url']
user_data, db_data = database_URL[11:].split('@')
user, password = user_data.split(':')
db_host, db_name = db_data.split('/')
dsn = f'dbname={db_name} user={user} password={password} host={db_host[:-5]}'

token = environ['token']
urls = ['https://youtu.be/gvTsB7GWpTc', 'https://youtu.be/Ii8850-G8S0']

leader_role_perms = discord.PermissionOverwrite(kick_members=True,
                                                mute_members=False,
                                                deafen_members=False,
                                                manage_channels=True,
                                                create_instant_invite=True)

default_role_perms = discord.PermissionOverwrite(connect=True,
                                                 speak=True,
                                                 use_voice_activation=True,
                                                 kick_members=False,
                                                 mute_members=False,
                                                 deafen_members=False,
                                                 manage_channels=False,
                                                 create_instant_invite=True)


def set_vars(bot):
    bot.create_channel = bot.get_channel(create_channel_id)
    bot.logger_channel = bot.get_channel(logger_id)
    bot.request_channel = bot.get_channel(role_request_id)
    bot.commands_channel = bot.get_channel(command_id)

    for category in categories:
        categories[category] = bot.get_channel(categories[category])  # rewrite categories dict
