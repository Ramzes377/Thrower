import discord
from discord.ext import commands

from api.bot.misc import now
from api.rest.v1.misc import sqllize, rm_keys
from api.bot.mixins import BaseCogMixin


class DBEvents(BaseCogMixin):
    async def _add_member(self, member: discord.Member):
        data = {'id': member.id, 'name': member.display_name, 'default_sess_name': None}
        await self.request('user/', 'post', json=data)

    def __init__(self, bot):
        super(DBEvents, self).__init__(bot, silent=True)
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
            await self.request(f'session/{channel_id}', 'patch', json=session)

    async def session_prescence(self, **prescence):
        prescence = sqllize(prescence)
        method = 'patch' if prescence.get('end') else 'post'  # update/create
        await self.request('prescence/', method, json=prescence)
        if method == 'post':
            channel_id = prescence["channel_id"]
            member_id = prescence["member_id"]
            await self.request(f'session/{channel_id}/members/{member_id}', 'post')

    async def member_activity(self, **activity):
        activity = sqllize(activity)
        method = 'patch' if activity.get('end') else 'post'  # update/create
        await self.request(f'activity/', method, json=activity)
