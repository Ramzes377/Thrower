import discord
from discord.ext import commands
from sqlalchemy.exc import PendingRollbackError

from api.rest.v1.misc import sqllize, rm_keys
from api.bot.mixins import BaseCogMixin


class dbEvents(BaseCogMixin):
    async def _add_member(self, member: discord.Member):
        data = {'id': member.id, 'name': member.display_name, 'default_sess_name': None}
        try:
            await self.request('user/', 'post', json=data)
        except Exception as e:
            pass

    def __init__(self, bot):
        super(dbEvents, self).__init__(bot, silent=True)
        for member in bot.guilds[0].members:
            self.bot.loop.create_task(self._add_member(member))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self._add_member(member)

    async def session_update(self, **sessiondata):
        data = sqllize(sessiondata)
        create_channel = data.get('creator_id') and data.get('begin')

        if create_channel:
            data['leader_id'] = data['creator_id']
            await self.request('session/', 'post', json=data)
            data['member_id'], *_ = rm_keys(data, 'leader_id', 'creator_id', 'message_id')
            await self.request('leadership/', 'post', json=data)
        else:  # change leader or end session
            leader_change = data.get('member_id') and data.get('end')
            if leader_change:
                await self.request('leadership/', 'post', json=data)
                data['leader_id'], *_ = rm_keys(data, 'member_id', 'end')
            channel_id = data.pop('channel_id')
            session = await self.request(f'session/{channel_id}')
            session.update(data)
            await self.request(f'session/{channel_id}', 'put', json=session)

    async def session_prescence(self, **prescencedata):
        prescence = sqllize(prescencedata)
        method = 'put' if prescence.get('end') else 'post'  # update/create
        await self.request('prescence/', method, json=prescence)
        if method == 'post':
            channel_id = prescencedata["channel_id"]
            member_id = prescencedata["member_id"]
            try:
                await self.request(f'session/{channel_id}/members/{member_id}', 'post')
            except PendingRollbackError:
                pass

    async def member_activity(self, channel_id: int, app_id: int, **activitydata):
        if channel_id:
            await self.request(f'session/{channel_id}/activities/{app_id}', 'post')
        activity = sqllize(activitydata)
        method = 'put' if activity.get('end') else 'post'  # update/create
        try:
            await self.request(f'activity/', method, json=activity)
        except Exception as e:
            pass
