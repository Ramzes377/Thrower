import asyncio

import discord

from api.cogs.tools.logger import Logger
from .tools.utils import flatten, get_category, user_is_playing, default_role_rights, \
    leader_role_rights, bots_ids, get_cur_user_channel
from .tools.mixins import BaseCogMixin, commands, DiscordFeaturesMixin


class ChannelsManager(BaseCogMixin, DiscordFeaturesMixin):
    def __init__(self, bot, logger):
        super(ChannelsManager, self).__init__(bot)
        self.logger_instance = logger

    async def handle_created_channels(self, period=60*30):
        while True:
            db_channels = flatten(await self.execute_sql("SELECT user_id, channel_id FROM CreatedSessions", fetch_all=True))
            for user_id, channel_id in db_channels:
                user = self.bot.get_user(user_id)
                channel = self.bot.get_channel(channel_id)
                user_in_channel = get_cur_user_channel(user)
                channel_exist = channel is not None
                if channel_exist and channel != user_in_channel:
                    await self.join_to_foreign(user, channel, user_in_channel)
            await asyncio.sleep(period)

    @commands.Cog.listener()
    async def on_presence_update(self, _, after: discord.member.Member):
        channel = await self.get_user_channel(after.id)
        user_have_channel = channel is not None
        is_user_playing = user_is_playing(after)
        if user_have_channel:
            if is_user_playing:
                await self.logger_instance.log_activity(after, channel)
            await self.edit_channel_name_category(after, channel)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.member.Member, _, after: discord.VoiceState):
        channel = await self.get_user_channel(member.id)
        user_join_create_channel = after.channel == self.bot.create_channel
        user_join_to_foreign = not (channel and after.channel == channel)
        if user_join_create_channel:
            await self.user_try_create_channel(member, channel)
        elif user_join_to_foreign:
            await self.join_to_foreign(member, channel, after.channel)

    async def user_try_create_channel(self, user: discord.member.Member, user_channel: discord.VoiceChannel):
        user_have_channel = user_channel is not None
        # if channel already exist
        if not user_have_channel:
            # create channel
            user_channel = await self.create_channel(user)
            # send session message
            await self.logger_instance.session_begin(user, user_channel)
        # just send user to his channel
        await user.move_to(user_channel)

    async def join_to_foreign(self, user: discord.member.Member,
                              user_channel: discord.VoiceChannel,
                              foreign_channel: discord.VoiceChannel):
        # User haven't channel and try to join to channel of another user
        user_have_channel = user_channel is not None
        user_stay_guild = foreign_channel is not None
        if user_have_channel:
            await self.leader_leave(user, user_channel)
        if user_stay_guild:
            await self.add_user_to_session(user, foreign_channel)

    async def create_channel(self, user: discord.member.Member):
        channel_name = await self.get_user_sess_name(user)
        category = get_category(user)
        permissions = {user.guild.default_role: default_role_rights, user: leader_role_rights}
        channel = await user.guild.create_voice_channel(channel_name, category=category, overwrites=permissions)
        await self.execute_sql(f'''INSERT INTO CreatedSessions (user_id, channel_id) VALUES ({user.id}, {channel.id})
                                        ON CONFLICT (user_id) DO UPDATE SET channel_id = {channel.id};
                                INSERT INTO SessionMembers (member_id, channel_id) VALUES ({user.id}, {channel.id})''')
        return channel

    async def add_user_to_session(self, user: discord.member.Member, channel: discord.VoiceChannel):
        try:
            await self.execute_sql(f'INSERT INTO SessionMembers (channel_id, member_id) VALUES ({channel.id}, {user.id})')
            # add new member to logging message
            await self.logger_instance.update_members(channel=channel)
        except:
            pass

    async def end_session(self, channel: discord.VoiceChannel):
        await self.logger_instance.session_over(channel)
        await channel.delete()

    async def leader_leave(self, leader: discord.member.Member, channel: discord.VoiceChannel):
        user_channel_empty = len(channel.members) == 0
        await self.end_session(channel) if user_channel_empty else await self.transfer_channel(leader, channel)

    async def transfer_channel(self, user: discord.member.Member, channel: discord.VoiceChannel):
        try:
            new_leader = [member for member in channel.members if member.id not in bots_ids][0]  # New leader of this channel
            overwrites = {user: default_role_rights, new_leader: leader_role_rights}
            await self.edit_channel_name_category(new_leader, channel, overwrites=overwrites)
            await self.execute_sql(f"UPDATE CreatedSessions SET user_id = {new_leader.id} WHERE channel_id = {channel.id}")
            await self.logger_instance.log_activity(new_leader, channel)
            await self.logger_instance.change_leader(new_leader.mention, channel.id)
        except IndexError:  # remain only bots in channel
            await self.end_session(channel)


async def setup(bot):
    logger = Logger()
    logger.set_bot(bot)
    manager = ChannelsManager(bot, logger)
    await bot.add_cog(manager)
    await asyncio.ensure_future(manager.handle_created_channels())
