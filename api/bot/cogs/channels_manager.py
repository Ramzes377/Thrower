import asyncio
from contextlib import suppress

import cachetools
import discord
from discord.ext import tasks, commands

from settings import bots_ids
from ..mixins import DiscordFeaturesMixin


class ChannelsManager(DiscordFeaturesMixin):
    CREATION_COOLDOWN = 10

    def __init__(self, bot: commands.Bot):
        super(ChannelsManager, self).__init__(bot)
        self._cache = cachetools.TTLCache(maxsize=1e4,
                                          ttl=self.CREATION_COOLDOWN)
        self.handle_created_channels.start()

    @tasks.loop(minutes=10)
    async def handle_created_channels(self):
        # handle channels sometimes to prevent possible accumulating errors on channel transfer
        # or if bot was offline for some reasons then calculate possible current behavior

        sessions = await self.db.get_unclosed_sessions()
        for session in sessions:
            if (channel := self.bot.get_channel(session['channel_id'])) is None:  # channel don't exist
                continue
            if (member := channel.guild.get_member(session['leader_id'])) \
                    in channel.members:  # user in own channel
                continue

            voice_channel = member.voice.channel if member.voice else None
            with suppress(discord.HTTPException):
                if voice_channel is not None:  # user join channel
                    self.bot.dispatch("member_join_channel", member.id,
                                      voice_channel.id)
                if self._is_empty_channel(channel):
                    await self.end_session(channel)

    @handle_created_channels.before_loop
    async def distribute_create_channel_members(self):
        if members := self.bot.channel.create.members:
            user = members[0]
            channel = await self.make_channel(user)
            for member in members:
                await member.move_to(channel)

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member,
                                 after: discord.Member):
        self.bot.dispatch("activity", before, after)
        if (channel := await self.get_user_channel(after.id)) is not None:
            await self.edit_channel_name_category(after, channel)

    @commands.Cog.listener()
    async def on_voice_state_update(
            self,
            member: discord.Member,
            before: discord.VoiceState,
            after: discord.VoiceState
    ):
        if before.channel == after.channel:  # handling only channel changing, not mute or deaf member
            return

        if after.channel == self.bot.channel.create:  # user join to create own channel
            await self.user_create_channel(member)
        elif (channel := await self.get_user_channel(
                member.id)) and member not in channel.members:
            # User join to foreign channel (leave considered the same)
            try:  # transfer user channel
                new_leader = next(member for member in channel.members if
                                  member.id not in bots_ids)
                self.bot.dispatch("activity", None, new_leader)
                self.bot.dispatch("leader_change", channel.id, new_leader)
                overwrites = {member: self.bot.permissions.default,
                              new_leader: self.bot.permissions.leader}
                await self.edit_channel_name_category(new_leader, channel,
                                                      overwrites=overwrites)
            except StopIteration:  # channel is "empty"
                await self.end_session(channel)

    async def user_create_channel(self, user: discord.Member):
        if await self.db.get_user_session(user.id) and self._cache.get(user.id):
            await user.send(
                f'Для создания нужно подождать {self.CREATION_COOLDOWN} секунд!',
                delete_after=10
            )
            await asyncio.sleep(self.CREATION_COOLDOWN)  # for too quickly channel creation

        channel = await self.make_channel(user)
        self._cache[user.id] = user.id  # create a cooldown for user
        await user.move_to(channel)  # send user to his channel
        self.bot.dispatch("session_begin", user, channel)

    async def make_channel(self, user: discord.Member) -> discord.VoiceChannel:
        name = await self.get_user_sess_name(user)
        category = self.get_category(user)
        permissions = {user: self.bot.permissions.leader,
                       user.guild.default_role: self.bot.permissions.default}
        channel = await user.guild.create_voice_channel(name, category=category,
                                                        overwrites=permissions)
        return channel

    async def end_session(self, channel: discord.VoiceChannel):
        with suppress(discord.NotFound):
            self.bot.dispatch("session_over", channel.id)
            await channel.delete()
