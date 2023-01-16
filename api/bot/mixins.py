import asyncio
import re
from typing import Awaitable

import discord
from discord.ext import commands

from api.rest.base import request
from .misc import get_category


class BaseCogMixin(commands.Cog):

    def __init__(self, bot, silent=False):
        super(BaseCogMixin, self).__init__()
        self.bot = bot
        if not silent:
            print(f'Cog {type(self).__name__} have been started!')

    @staticmethod
    def exist(obj: dict):
        return obj is not None and 'detail' not in obj

    @staticmethod
    async def request(url: str, method: str = 'get', data: dict | None = None):
        try:
            return await request(url, method, data)
        except Exception as e:
            if 'user/' in url:
                return
            print(f'Raised exception {e=} with follows params: \n{url=}, \n{method=}, \n{data=}')

    async def log_message(self, send: Awaitable):
        msg = await send
        await self.request(f'sent_message/', 'post', data={'id': msg.id})
        return msg


class BasicRequests(BaseCogMixin):

    async def update_leader(self, *args, channel_id, member_id, begin, update_sess=True, **kwargs) -> None:
        if update_sess and member_id is not None:  # close session
            await self.session_update(channel_id=channel_id, leader_id=member_id)
        data = {'channel_id': channel_id, 'member_id': member_id, 'begin': begin}
        await self.request('leadership/', 'post', data=data)

    async def member_activity(self, **activity: dict[int | str]) -> None:
        method = 'patch' if activity.get('end') else 'post'  # update/create
        await self.request(f'activity/', method, data=activity)

    async def session_update(self, **session: dict[int | str]) -> dict:
        create_channel = session.get('creator_id')

        if create_channel:  # create
            sess = await self.request('session/', 'post', data=session)
            await self.update_leader(channel_id=session['channel_id'], member_id=session['leader_id'],
                                     begin=session['begin'], update_sess=False)
        else:  # update
            channel_id = session.pop('channel_id')  # pop it to not override it into db
            sess = await self.request(f'session/{channel_id}', 'patch', data=session)
        return sess

    async def user_create(self, **user: dict[int | str]) -> None:
        await self.request('user/', 'post', data=user)

    async def user_update(self, **user: dict[int | str]) -> None:
        user_id: int = user.pop('id')
        await self.request(f'user/{user_id}', 'patch', data=user)

    async def role_create(self, role_id: int, app_id: int) -> dict:
        await self.request('role/', 'post', data={'id': role_id, 'app_id': app_id})

    async def role_delete(self, role_id: int) -> dict:
        return await self.request(f'role/{role_id}', 'delete')

    async def emoji_create(self, emoji_id: int, role_id: int) -> dict:
        await self.request('emoji/', 'post', data={'id': emoji_id, 'role_id': role_id})

    async def music_create(self, data: dict) -> dict:
        return await self.request(f'favoritemusic/', 'post', data=data)

    async def prescence_update(self, **prescence) -> None:
        method = 'patch' if prescence.get('end') else 'post'  # update/create
        await self.request('prescence/', method, data=prescence)

    async def session_add_member(self, channel_id: int, member_id: int):
        await self.request(f'session/{channel_id}/members/{member_id}', 'post')

    async def create_sent_message(self, msg_id: int):
        return await self.request(f'sent_message/', 'post', data={'id': msg_id})

    async def get_member(self, member_id: int) -> dict:
        return await self.request(f'user/{member_id}')

    async def get_session(self, channel_id: int) -> dict:
        return await self.request(f'session/{channel_id}')

    async def get_unclosed_sessions(self) -> list[dict]:
        return await self.request(f'session/unclosed/')

    async def get_user_session(self, user_id: int) -> dict:
        return await self.request(f'session/unclosed/{user_id}')

    async def get_all_sessions(self) -> list[dict]:
        return await self.request('session/')

    async def get_session_members(self, session_id: int) -> list[dict]:
        return await self.request(f'session/{session_id}/members')

    async def get_activity_info(self, app_id: int) -> dict:
        return await self.request(f'activity/{app_id}/info')

    async def get_activity_emoji(self, app_id: int) -> dict:
        return await self.request(f'activity/{app_id}/emoji')

    async def get_activity_duration(self, user_id: int, role_id: int) -> dict:
        return await self.request(f'user/{user_id}/activities/duration/{role_id}')

    async def get_emoji_role(self, emoji_id: int) -> dict:
        return await self.request(f'emoji/{emoji_id}/role')

    async def get_role(self, app_id: int) -> dict:
        return await self.request(f'role/by_app/{app_id}')

    async def get_activityinfo(self, app_id: int) -> dict:
        return await self.request(f'activityinfo/{app_id}')

    async def get_user_favorite_music(self, user_id: int) -> dict:
        return await self.request(f'favoritemusic/{user_id}')

    async def get_session_leadership(self, message_id: int) -> list[dict]:
        return await self.request(f'session/{message_id}/leadership')

    async def get_session_activities(self, message_id: int) -> list[dict]:
        return await self.request(f'session/{message_id}/activities')

    async def get_session_prescence(self, message_id: int) -> list[dict]:
        return await self.request(f'session/{message_id}/prescence')


class DiscordFeaturesMixin(BasicRequests):
    async def get_user_channel(self, user_id: int) -> discord.VoiceChannel | None:
        session = await self.get_user_session(user_id)
        return self.bot.get_channel(session['channel_id']) if self.exist(session) else None

    async def get_user_sess_name(self, user: discord.member.Member) -> str:
        if user.activity and user.activity.type is discord.ActivityType.playing:
            sess_name = f"[{re.compile('[^a-zA-Z0-9а-яА-Я +]').sub('', user.activity.name)}]"
        else:
            member = await self.get_member(user.id)
            if member.get('default_sess_name'):
                sess_name = member['default_sess_name']
            else:
                session = await self.get_user_session(user.id)
                sess_name = session['name'] if self.exist(session) else f"Сессия {user.display_name}'а"
        return sess_name

    async def edit_channel_name_category(self, user: discord.member.Member, channel: discord.VoiceChannel,
                                         overwrites=None) -> None:
        channel_name = await self.get_user_sess_name(user)
        category = get_category(user)
        try:
            await asyncio.wait_for(
                channel.edit(name=channel_name, category=category, overwrites=overwrites),
                timeout=5.0
            )
        except asyncio.TimeoutError:  # Trying to rename channel in transfer but Discord restrictions :('
            await channel.edit(category=category, overwrites=overwrites)
        except discord.NotFound:
            pass
