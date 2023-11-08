from api.dependencies import default_period
from bot.meta import GettersWrapping
from utils import request


class BasicRequests(metaclass=GettersWrapping):

    async def update_leader(
            self,
            *,
            channel_id,
            member_id,
            begin,
            update_sess=True
    ) -> None:
        if update_sess and member_id is not None:  # close session
            await self.session_update(
                channel_id=channel_id,
                leader_id=member_id
            )
        data = dict(channel_id=channel_id, member_id=member_id, begin=begin)
        await request('leadership', 'post', data=data)

    async def member_activity(self, **activity: dict[int | str]) -> None:
        method = 'patch' if activity.get('end') else 'post'  # update/create
        await request('activity', method, data=activity)

    async def session_update(self, **session: dict[int | str]) -> dict:
        create_channel = session.get('creator_id')

        if create_channel:  # create
            sess = await request('session', 'post', data=session)
            await self.update_leader(
                channel_id=session['channel_id'],
                member_id=session['leader_id'],
                begin=session['begin'],
                update_sess=False,
            )
        else:  # update
            channel_id = session.pop('channel_id')
            sess = await request(
                f'session/{channel_id}',
                'patch', data=session,
            )
        return sess

    async def user_create(self, **user: dict[int | str]) -> None:
        await request('user', 'post', data=user)

    async def user_update(self, **user: dict[int | str: int | str]) -> None:
        user_id: int = user.pop('id')
        await request(f'user/{user_id}', 'patch', data=user)

    async def role_create(self, role_id: int, app_id: int, guild_id: int):
        await request(
            'role',
            'post',
            data={'id': role_id, 'app_id': app_id, 'guild_id': guild_id}
        )

    async def role_delete(self, role_id: int) -> dict:
        return await request(f'role/{role_id}', 'delete')

    async def emoji_create(self, emoji_id: int, role_id: int):
        await request(
            'emoji',
            'post',
            data={'id': emoji_id, 'role_id': role_id}
        )

    async def music_create(self, data: dict) -> dict:
        return await request(f'favorite_music', 'post', data=data)

    async def prescence_update(self, **prescence) -> None:
        method = 'patch' if prescence.get('end') else 'post'  # update/create
        await request('prescence', method, data=prescence)

    async def session_add_member(self, channel_id: int, member_id: int):
        r = await request(
            f'session/{channel_id}/members/{member_id}',
            'post'
        )
        if 'detail' in r:
            raise ValueError('Session still not exist probably!')
        return r

    async def create_sent_message(self, msg_id: int):
        return await request(
            f'sent_message',
            'post',
            data={'id': msg_id}
        )

    async def get_member(self, member_id: int) -> dict:
        return await request(f'user/{member_id}')

    async def get_session(self, channel_id: int) -> dict:
        return await request(f'session/{channel_id}')

    async def get_unclosed_sessions(self) -> list[dict]:
        return await request(f'session/unclosed')

    async def get_user_session(self, user_id: int) -> dict:
        return await request(f'session/unclosed/{user_id}')

    async def get_all_sessions(self, begin=None, end=None) -> list[dict]:
        return await request(
            'session',
            params=default_period(begin, end)
        )

    async def get_session_members(self, session_id: int) -> list[dict]:
        return await request(f'session/{session_id}/members')

    async def get_activity_info(self, app_id: int) -> dict:
        return await request(f'activity/{app_id}/info')

    async def get_activity_emoji(self, app_id: int) -> dict:
        return await request(f'activity/{app_id}/emoji')

    async def get_activity_duration(self, user_id: int, role_id: int) -> dict:
        url = f'user/{user_id}/activities/duration/{role_id}'
        return await request(url)

    async def get_emoji_role(self, emoji_id: int) -> dict:
        return await request(f'emoji/{emoji_id}/role')

    async def get_role(self, app_id: int, guild_id: int) -> dict:
        return await request(f'role/by_app/{app_id}',
                             params={'guild_id': guild_id})

    async def get_all_roles(self) -> dict:
        return await request(f'role')

    async def get_role_id(self, role_id: int) -> dict:
        return await request(f'role/{role_id}')

    async def get_activityinfo(self, app_id: int) -> dict:
        return await request(f'activity_info/{app_id}')

    async def get_user_favorite_music(self, user_id: int) -> dict:
        return await request(f'favorite_music/{user_id}')

    async def get_session_leadership(self, message_id: int) -> list[dict]:
        return await request(f'session/{message_id}/leadership')

    async def get_session_activities(self, message_id: int) -> list[dict]:
        return await request(f'session/{message_id}/activities')

    async def get_session_prescence(self, message_id: int) -> list[dict]:
        return await request(f'session/{message_id}/prescence')

    async def post_guild_ids(self, data: dict) -> int | None:
        r = await request('guild', 'post', data=data)
        return r['id'] if r else None
