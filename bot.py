import discord
from discord.ext import commands

from api.rest.base import request
from settings import envs, token, guild, categories, intents

bot = commands.Bot(command_prefix='!', intents=intents, fetch_offline_members=False)


@bot.event
async def on_ready():
    bot.create_channel = bot.get_channel(envs['create_channel_id'])
    bot.logger_channel = bot.get_channel(envs['logger_id'])
    bot.request_channel = bot.get_channel(envs['role_request_id'])
    bot.commands_channel = bot.get_channel(envs['command_id'])

    for category in categories:
        categories[category] = bot.get_channel(categories[category])

    await bot.load_extension('api.bot.__init__')
    print(await bot.tree.sync(guild=guild))

    await clear_unregistered_messages()
    print('Bot have been started!')


@bot.tree.error
async def on_command_error(ctx, error):
    print(ctx, error)


async def clear_unregistered_messages():
    guild = bot.get_guild(envs['guild_id'])
    text_channels = [channel for channel in guild.channels if channel.type.name == 'text']
    messages = await request('sent_message/')
    for message in messages:
        for channel in text_channels:
            try:
                if msg := await channel.fetch_message(message['id']):
                    print(msg)
                    # deletion process
                    # await msg.delete()
                else:
                    print(await request(f'sent_message/{msg.id}', 'delete'))
            except discord.NotFound:
                pass


def run():
    bot.run(token, reconnect=True)
