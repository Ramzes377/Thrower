import discord
from discord.ext import commands

from api.rest.v1.misc import sqllize, rm_keys
from api.bot.mixins import BaseCogMixin


class dbEvents(BaseCogMixin):
    def __init__(self, bot):
        super(dbEvents, self).__init__(bot, silent=True)
        for member in bot.guilds[0].members:
            self._add_member(member)

    def _add_member(self, member: discord.Member):
        data = {'id': member.id, 'name': member.display_name, 'default_sess_name': None}
        try:
            self._client.post('/v1/user/', json=data)
        except Exception as e:
            pass

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        self._add_member(member)

    def session_update(self, **sessiondata):
        data = sqllize(sessiondata)
        create_channel = data.get('creator_id') and data.get('begin')

        if create_channel:
            data['leader_id'] = data['creator_id']
            self._client.post('v1/session/', json=data)
            data['member_id'], *_ = rm_keys(data, 'leader_id', 'creator_id', 'message_id')
            self._client.post(f'v1/leadership', json=data)
        else:  # change leader or end session
            leader_change = data.get('member_id') and data.get('end')
            if leader_change:
                self._client.post(f'v1/leadership', json=data)
                data['leader_id'], *_ = rm_keys(data, 'member_id', 'end')
            channel_id = data.pop('channel_id')
            session = self._client.get(f'v1/session/{channel_id}').json()
            session.update(data)
            self._client.put(f'v1/session/{channel_id}', json=session)

    def session_prescence(self, **prescencedata):
        prescence = sqllize(prescencedata)
        method = 'put' if prescence.get('end') else 'post'  # update/create
        self._client.request(method, 'v1/prescence/', json=prescence)
        if method == 'post':
            channel_id = prescencedata["channel_id"]
            member_id = prescencedata["member_id"]
            self._client.post(f'v1/session/{channel_id}/members/{member_id}')

    def member_activity(self, channel_id: int, app_id: int, **activitydata):
        if channel_id:
            self._client.post(f'v1/session/{channel_id}/activities/{app_id}')
        activity = sqllize(activitydata)
        method = 'put' if activity.get('end') else 'post'  # update/create
        try:
            self._client.request(method, 'v1/activity/', json=activity)
        except Exception as e:
            pass
