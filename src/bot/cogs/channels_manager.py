import asyncio
from contextlib import suppress
from typing import TYPE_CHECKING

import cachetools
from discord import HTTPException, NotFound
from discord.ext import tasks, commands

from src.constants import constants
from src.bot.mixins import DiscordFeaturesMixin
from src.config import Config

if TYPE_CHECKING:
    from discord import VoiceChannel, VoiceState, Member


class ChannelsManager(DiscordFeaturesMixin):

    def __init__(self, bot: commands.Bot):
        super(ChannelsManager, self).__init__(bot)
        self._cache = cachetools.TTLCache(maxsize=1e4,
                                          ttl=Config.creation_cooldown)
        self.handle_created_channels.start()

    @tasks.loop(minutes=10)
    async def handle_created_channels(self):
        """
        Handle channels sometimes to prevent possible accumulating errors
        on channel transfer or if bot was offline for source reason then
        calculate possible current behavior
        """

        sessions = await self.db.get_unclosed_sessions()
        for session in sessions:
            if (channel := self.bot.get_channel(session['channel_id'])) is None:
                continue  # channel don't exist
            if (member := channel.guild.get_member(session['leader_id'])) \
                    in channel.members:  # user in own channel
                continue

            voice_channel = member.voice.channel if member.voice else None
            with suppress(HTTPException):
                if voice_channel is not None:  # user join channel
                    self.bot.dispatch(
                        "member_join_channel",
                        member.id,
                        voice_channel
                    )
                if self._is_empty_channel(channel):
                    await self.end_session(channel)

        # FIXME: need upgrade

    @handle_created_channels.before_loop
    async def distribute_create_channel_members(self) -> None:
        for guild_id, channels in self.bot.guild_channels.items():
            if members := channels.create.members:
                user = members[0]
                channel = await self.make_channel(user, guild_id)
                for member in members:
                    await member.move_to(channel)

    @commands.Cog.listener()
    async def on_presence_update(
            self,
            before: 'Member',
            after: 'Member'
    ):
        self.bot.dispatch("activity", before, after)

    @commands.Cog.listener()
    async def on_voice_state_update(self,
                                    member: 'Member',
                                    before: 'VoiceState',
                                    after: 'VoiceState'):
        if before.channel == after.channel:
            # handling only channel changing, not mute or deaf member
            return

        channel = after.channel or before.channel
        guild_id = channel.guild.id
        if (guild_channels := self.bot.guild_channels.get(guild_id)) is None:
            return

        create_channel = guild_channels.create

        if after.channel == create_channel:
            # user join to create own channel
            await self.user_create_channel(member, guild_id)
        elif ((channel := await self.get_user_channel(member.id))
              and member not in channel.members):
            # User join to foreign channel (leave considered the same)
            if not self._is_empty_channel(channel):  # transfer user channel
                new_leader = next(
                    member for member in channel.members if not member.bot
                )
                self.bot.dispatch("activity", None, new_leader)
                self.bot.dispatch("leader_change", channel, new_leader)
                overwrites = {member: self.bot.permissions.default,
                              new_leader: self.bot.permissions.leader}
                await self.edit_channel_name_category(
                    new_leader,
                    channel,
                    overwrites=overwrites
                )
            else:  # channel is "empty"
                await self.end_session(channel)

    async def user_create_channel(self, user: 'Member', guild_id: int):
        if await self.db.get_user_session(user.id) and self._cache.get(user.id):
            await user.send(
                constants.wait_cooldown(cooldown=Config.creation_cooldown),
                delete_after=10
            )
            # for too quickly channel creation
            await asyncio.sleep(Config.creation_cooldown)

        channel = await self.make_channel(user, guild_id)

        self.bot.loop.create_task(
            user.move_to(channel))  # send user to his channel
        self.bot.dispatch("session_begin", user, channel)

        self._cache[user.id] = user.id  # create a cooldown for user

    async def make_channel(self,
                           user: 'Member',
                           guild_id: int,
                           ) -> 'VoiceChannel':

        name = await self.get_user_sess_name(user)
        category = self.get_category(user, guild_id)
        permissions = {
            user: self.bot.permissions.leader,
            user.guild.default_role: self.bot.permissions.default
        }
        channel = await user.guild.create_voice_channel(name,
                                                        category=category,
                                                        overwrites=permissions)
        return channel

    async def end_session(self, channel: 'VoiceChannel'):
        with suppress(NotFound):
            self.bot.dispatch("session_over", channel)
            await channel.delete()
