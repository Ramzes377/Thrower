from contextlib import suppress

import discord
from discord.ext import tasks, commands

from settings import bots_ids, default_role_perms, leader_role_perms
from ..mixins import DiscordFeaturesMixin


class ChannelsManager(DiscordFeaturesMixin):
    def __init__(self, bot: commands.Bot):
        super(ChannelsManager, self).__init__(bot)
        self.handle_created_channels.start()

    @staticmethod
    def _is_empty_channel(channel: discord.VoiceChannel):
        members = channel.members
        is_empty = len(members) == 0
        return True if is_empty else all(channel.guild.get_member(id) in members for id in bots_ids)

    @tasks.loop(minutes=10)
    async def handle_created_channels(self):
        # handle channels sometimes to prevent possible accumulating errors on channel transfer
        # or if bot was offline for some reasons then calculate possible current behavior

        sessions = await self.db.get_unclosed_sessions()
        for session in sessions:
            if (channel := self.bot.get_channel(session['channel_id'])) is None:
                continue
            guild = channel.guild
            member = guild.get_member(session['leader_id'])
            if not (channel and member in channel.members):  # user_in_own_channel
                voice_channel = member.voice.channel if member.voice else None
                with suppress(discord.HTTPException):
                    if voice_channel is not None:  # user join channel
                        self.bot.dispatch("member_join_channel", member.id, voice_channel.id)
                    if self._is_empty_channel(channel):
                        await self.end_session(channel)

    @handle_created_channels.before_loop
    async def distribute_create_channel_members(self):
        if members := self.bot.create_channel.members:
            user = members[0]
            channel = await self.make_channel(user)
            for member in members:
                await member.move_to(channel)

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        self.bot.dispatch("activity", before, after)
        if (channel := await self.get_user_channel(after.id)) is not None:
            await self.edit_channel_name_category(after, channel)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        if before.channel == after.channel or before.channel == self.bot.create_channel:
            # handling only channel changing, not mute or deaf member
            # and previous channel is not 'create' channel
            return

        if after.channel == self.bot.create_channel:  # user join to create own channel
            await self.user_create_channel(member)
        elif not ((channel := await self.get_user_channel(member.id)) and after.channel == channel):
            # User join to foreign channel (leave considered the same)
            if after.channel is not None:  # user join channel
                self.bot.dispatch("member_join_channel", member.id, after.channel.id)

            if before.channel is not None:  # user leave
                self.bot.dispatch("member_abandon_channel", member.id, before.channel.id)

            if channel is not None and not self._is_empty_channel(channel):  # transfer user channel
                new_leader = next(member for member in channel.members)
                overwrites = {member: default_role_perms, new_leader: leader_role_perms}
                await self.edit_channel_name_category(new_leader, channel, overwrites=overwrites)
                self.bot.dispatch("activity", None, new_leader)
                self.bot.dispatch("leader_change", channel.id, new_leader.id)

    async def user_create_channel(self, user: discord.Member):
        channel = await self.make_channel(user)
        await user.move_to(channel)  # send user to his channel
        self.bot.dispatch("session_begin", user.id, channel)

        def check(event_user, before, after):
            return self._is_empty_channel(channel)

        await self.bot.wait_for('voice_state_update', check=check)
        await self.end_session(channel)

    async def make_channel(self, user: discord.Member) -> discord.VoiceChannel:
        channel_name = await self.get_user_sess_name(user)
        permissions = {user: leader_role_perms, user.guild.default_role: default_role_perms}
        channel = await user.guild.create_voice_channel(channel_name,
                                                        category=self.get_category(user),
                                                        overwrites=permissions)
        return channel

    async def end_session(self, channel: discord.VoiceChannel):
        with suppress(discord.NotFound):
            self.bot.dispatch("session_over", channel.id)
            await channel.delete()
