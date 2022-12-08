import asyncio

import discord
from discord.ext import tasks

from api.bot.logger.logger import Logger
from api.bot.misc import get_category
from api.bot.mixins import commands, DiscordFeaturesMixin
from api.bot.vars import default_role_perms, leader_role_perms, bots_ids

CREATED_CHANNELS_HANDLE_PERIOD = 30 * 60  # in seconds


class ChannelsManager(DiscordFeaturesMixin):
    channel_flags = {}

    def __init__(self, bot: commands.Bot):
        super(ChannelsManager, self).__init__(bot)
        self.logger = Logger(bot)
        self.handle_created_channels.start()

    @tasks.loop(seconds=CREATED_CHANNELS_HANDLE_PERIOD)
    async def handle_created_channels(self):
        # handle channels every 30 minutes to prevent possible accumulating errors on channel transfer
        # or if bot was offline for some reasons then calculate possible current behavior
        guild = self.bot.guilds[0]
        sessions = self._client.get('v1/session/unclosed/').json()
        for session in sessions:
            user = self.bot.get_user(session['leader_id'])
            channel = self.bot.get_channel(session['channel_id'])
            user_in_own_channel = channel and user in channel.members
            if not user_in_own_channel:
                cur_channel = [guild_channel for guild_channel in guild.voice_channels if
                               user in guild_channel.members]
                cur_channel = cur_channel[0] if len(cur_channel) > 0 else None
                await self.join_to_foreign(user, channel, None, cur_channel)

    @handle_created_channels.before_loop
    async def distribute_created_channel(self):
        members = self.bot.create_channel.members
        if members:
            user = members[0]
            channel = await self.create_channel(user)
            for member in members:
                try:
                    await member.move_to(channel)
                except:
                    pass

        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        await self.logger.log_activity(before, after)
        channel = self.get_user_channel(after.id)
        if channel is not None:
            ChannelsManager.channel_flags[channel.id] = 'A'
            await self.edit_channel_name_category(after, channel)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.VoiceChannel, after: discord.VoiceChannel):
        # skip transfer channel rename and activity rename
        await asyncio.sleep(3)  # delay to prevent skip event of activity or transfer channel
        channel_state = ChannelsManager.channel_flags.pop(after.id, None)
        need_save = channel_state not in ('T', 'A')
        if need_save and before.name != after.name:
            session = self._client.get(f'v1/session/{after.id}').json()
            self._client.put(f'v1/user/{session["leader_id"]}', json={'default_sess_name': after.name})

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        if before.channel == after.channel or before.channel == self.bot.create_channel:
            # handling only channel changing, not mute or deaf member
            # and previous channel is not create channel
            return
        channel = self.get_user_channel(member.id)
        user_join_create_channel = after.channel == self.bot.create_channel
        user_join_to_foreign = not (channel and after.channel == channel)  # user join not to own channel

        if user_join_create_channel:
            await self.user_try_create_channel(member, channel)
        elif user_join_to_foreign:
            await self.join_to_foreign(member, channel, before.channel, after.channel)

    async def user_try_create_channel(self, user: discord.Member, user_channel: discord.VoiceChannel):
        user_have_channel = user_channel is not None
        if user_have_channel:  # if channel already exist
            await user.move_to(user_channel)
            return

        user_channel = await self.create_channel(user)
        await user.move_to(user_channel)  # send user to his channel
        await self.logger.session_begin(user.id, user_channel)  # send session message

    async def create_channel(self, user: discord.Member) -> discord.VoiceChannel:
        channel_name = self.get_user_sess_name(user)
        category = get_category(user)
        permissions = {user.guild.default_role: default_role_perms, user: leader_role_perms}
        channel = await user.guild.create_voice_channel(channel_name, category=category, overwrites=permissions)
        return channel

    async def join_to_foreign(self, user: discord.Member,
                              user_channel: discord.VoiceChannel,
                              prev_channel: discord.VoiceChannel,
                              cur_channel: discord.VoiceChannel):
        # User try to join to channel of another user or leave
        user_have_channel = user_channel is not None
        user_join_channel = cur_channel is not None
        user_quit_channel = prev_channel is not None

        if user_quit_channel:
            await self.logger.log_member_abandon(user.id, prev_channel.id)

        if user_join_channel:
            await self.logger.log_member_join(user.id, cur_channel.id)

        if user_have_channel:
            await self.leader_leave(user, user_channel)

    async def leader_leave(self, leader: discord.Member, channel: discord.VoiceChannel):
        user_channel_empty = len(channel.members) == 0
        await self.end_session(channel) if user_channel_empty else await self.transfer_channel(leader, channel)

    async def transfer_channel(self, user: discord.Member, channel: discord.VoiceChannel):
        try:
            new_leader = [member for member in channel.members if member.id not in bots_ids][0]
            overwrites = {user: default_role_perms, new_leader: leader_role_perms}
            await self.edit_channel_name_category(new_leader, channel, overwrites=overwrites)
            await self.logger.log_activity(None, new_leader)
            await self.logger.update_leader(channel.id, new_leader.id)
            ChannelsManager.channel_flags[channel.id] = 'T'
        except IndexError:  # remain only bots in channel
            await self.end_session(channel)

    async def end_session(self, channel: discord.VoiceChannel):
        await self.logger.session_over(channel.id)
        await channel.delete()


async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelsManager(bot))
