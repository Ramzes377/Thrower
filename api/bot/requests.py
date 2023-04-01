from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from api.rest.base import request
from api.rest.v1.dependencies import default_period


def exist(obj: dict) -> bool:
    return obj is not None and 'detail' not in obj


def deco(func):
    async def wrapper(*args, **kwargs):
        res = await func(*args, **kwargs)
        if not exist(res):
            res = None
        return res
    return wrapper


class GettersWrapping(type):
    def __new__(cls, name, bases, attrs):
        new_attrs = {}
        include = ['session_add_member']
        for attr_name, attr_value in attrs.items():
            if callable(attr_value) and (attr_name.startswith('get_') or attr_name in include):
                new_attrs[attr_name] = deco(attr_value)
            else:
                new_attrs[attr_name] = attr_value
        return super().__new__(cls, name, bases, new_attrs)


class BasicRequests(metaclass=GettersWrapping):
    @staticmethod
    async def request(url: str, method: str = 'get', data: dict | None = None,
                      params: dict | None = None) -> dict | None:
        try:
            return await request(url, method, data, params)
        except Exception as e:
            print(f'Raised exc {e}. {url} {method} {data} {params}')
            raise e

    async def update_leader(self, *, channel_id, member_id, begin, update_sess=True) -> None:
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
        return await self.request(f'session/{channel_id}/members/{member_id}', 'post')

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

    async def get_all_sessions(self, begin=None, end=None) -> list[dict]:
        return await self.request('session/', params=default_period(begin, end))

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

    async def get_all_roles(self) -> dict:
        return await self.request(f'role/')

    async def get_role_id(self, role_id: int) -> dict:
        return await self.request(f'role/{role_id}')

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
