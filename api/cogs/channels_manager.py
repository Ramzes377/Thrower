from .tools.utils import flatten, get_category, user_is_playing, get_activity_name, default_role_rights, \
    leader_role_rights, bots_ids, get_cur_user_channel, edit_channel_name_category
from .tools.base_cog import BaseCog, commands


class ChannelsManager(BaseCog):
    logger_instance = None
    gamerole_instance = None

    @commands.Cog.listener()
    async def on_ready(self):
        await self.startup_channels_handle()

    async def startup_channels_handle(self):
        db_channels = flatten(await self.execute_sql("SELECT user_id, channel_id FROM CreatedSessions"))
        for user_id, channel_id in db_channels:
            user = self.bot.get_user(user_id)
            channel = self.bot.get_channel(channel_id)
            user_in_channel = get_cur_user_channel(user)
            channel_exist = channel is not None
            if channel_exist and channel != user_in_channel:
                await self.join_to_foreign(user, channel, user_in_channel)

    @commands.Cog.listener()
    async def on_presence_update(self, _, after):
        await self.show_activity(after)

    async def show_activity(self, user):
        channel = await self.get_user_channel(user.id)
        channel_exist = channel is not None
        if user_is_playing(user):
            if channel_exist:
                await edit_channel_name_category(user, channel)
                await self.logger_instance.log_activity(user, channel)
            await self.gamerole_instance.add_gamerole(user)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, _, after):
        channel = await self.get_user_channel(member.id)  # try to get user's channel
        user_join_create_channel = after.channel == self.bot.create_channel
        user_join_own_channel = channel and after.channel == channel
        if user_join_create_channel:
            await self.user_try_create_channel(member, channel)
        elif not user_join_own_channel:
            await self.join_to_foreign(member, channel, after.channel)

    async def user_try_create_channel(self, user, user_channel):
        user_have_channel = user_channel is not None
        if not user_have_channel:  # if channel already exist
            user_channel = await self.create_channel(user)  # create channel
            await self.logger_instance.session_begin_msg(user, user_channel)  # send session message
        await user.move_to(user_channel)  # just send user to his channel

    async def create_channel(self, user):
        default_sess_name = await self.execute_sql(f'SELECT name FROM UserDefaultSessionName WHERE user_id = {user.id}')
        channel_name = default_sess_name[0] if default_sess_name and default_sess_name[0] else get_activity_name(user)
        category = get_category(user)
        permissions = {user.guild.default_role: default_role_rights, user: leader_role_rights}
        channel = await user.guild.create_voice_channel(channel_name, category=category, overwrites=permissions)
        await self.execute_sql(f'''INSERT INTO CreatedSessions (user_id, channel_id) VALUES ({user.id}, {channel.id})
                                        ON CONFLICT (user_id) DO UPDATE SET channel_id = {channel.id}''',
                               f"INSERT INTO SessionMembers (member_id, channel_id) VALUES ({user.id}, {channel.id})")
        return channel

    async def join_to_foreign(self, user, user_channel,
                              foreign_channel):  # User haven't channel and try to join to channel of another user
        user_have_channel = user_channel is not None
        user_leave_guild = foreign_channel is None
        if user_have_channel:
            await self.leader_leave(user, user_channel)
        if not user_leave_guild:  # user not just leave from server
            try:
                await self.execute_sql(f'INSERT INTO SessionMembers (channel_id, member_id) VALUES ({foreign_channel.id}, {user.id})')
                await self.logger_instance.log_msg_update_members(channel=foreign_channel)  # add new member to logger message
            except:
                pass

    async def end_session(self, channel):
        await self.logger_instance.session_over_msg(channel)
        await channel.delete()

    async def leader_leave(self, leader, channel):
        user_channel_empty = not channel.members
        await self.end_session(channel) if user_channel_empty else await self.transfer_channel(leader, channel)

    async def transfer_channel(self, user, channel):
        try:
            new_leader = [member for member in channel.members if member.id not in bots_ids][0]  # New leader of this channel
            overwrites = {user: default_role_rights, new_leader: leader_role_rights}
            await edit_channel_name_category(new_leader, channel, overwrites=overwrites)
            await self.execute_sql(f"UPDATE CreatedSessions SET user_id = {new_leader.id} WHERE channel_id = {channel.id}")
            await self.logger_instance.log_activity(new_leader, channel)
            await self.logger_instance.log_msg_change_leader(new_leader.mention, channel.id)
        except IndexError:  # remain only bots in channel
            await self.end_session(channel)

    def set_logger_instance(self, logger):
        self.logger_instance = logger

    def set_gamerole_instance(self, gamerole):
        self.gamerole_instance = gamerole


async def setup(bot):
    cog = ChannelsManager(bot)
    await bot.add_cog(cog)
    cog.set_logger_instance(bot.get_cog('Logger'))
    cog.set_gamerole_instance(bot.get_cog('GameRolesManager'))
