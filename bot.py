import discord
from discord.ext import commands

from settings import token, Permissions, _init_channels, _init_categories, clear_unregistered_messages

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all(), fetch_offline_members=False)


@bot.event
async def on_ready():
    bot.permissions = Permissions
    bot.channel = _init_channels(bot)
    bot.categories = _init_categories(bot)

    await bot.load_extension('api.bot')
    await bot.tree.sync()
    await clear_unregistered_messages(bot)

    print('Bot have been started!')


@bot.tree.error
async def on_command_error(ctx, error):
    pass  # useless message about command not found


def run():
    bot.run(token, reconnect=True)
