from sqlalchemy.exc import IntegrityError
import discord
from discord.ext import commands

from api.bot.mixins import BaseCogMixin


class DBEvents(BaseCogMixin):
    async def _add_member(self, member: discord.Member):
        data = {'id': member.id, 'name': member.display_name}
        try:
            await self.request('user/', 'post', data=data)
        except:
            pass

    def __init__(self, bot):
        super(DBEvents, self).__init__(bot, silent=True)
        for member in bot.guilds[0].members:
            self.bot.loop.create_task(self._add_member(member))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self._add_member(member)

    async def update_leader(self, *args, channel_id, member_id, begin, update_sess=True, **kwargs):
        if update_sess and member_id is not None:  # close session
            await self.session_update(channel_id=channel_id, leader_id=member_id)
        data = {'channel_id': channel_id, 'member_id': member_id, 'begin': begin}
        await self.request('leadership/', 'post', data=data)

    async def member_activity(self, **activity):
        method = 'patch' if activity.get('end') else 'post'  # update/create
        await self.request(f'activity/', method, data=activity)

    async def session_update(self, **session_data):
        data = session_data
        create_channel = data.get('creator_id')

        if create_channel:  # create
            session = await self.request('session/', 'post', data=data)
            await self.update_leader(channel_id=data['channel_id'], member_id=data['leader_id'], begin=data['begin'],
                                     update_sess=False)
        else:  # update
            channel_id = data.pop('channel_id')  # pop it to not override it into db
            session = await self.request(f'session/{channel_id}', 'patch', data=data)
        return session

    async def session_add_member(self, channel_id: int, member_id: int):
        try:
            await self.request(f'session/{channel_id}/members/{member_id}', 'post')
        except IntegrityError:
            pass

    async def session_prescence(self, **prescence):
        method = 'patch' if prescence.get('end') else 'post'  # update/create
        await self.request('prescence/', method, data=prescence)
        if method == 'post':
            await self.session_add_member(prescence['channel_id'], prescence['member_id'])
