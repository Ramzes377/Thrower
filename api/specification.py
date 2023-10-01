class Specification:
    column_name = None
    _id = None

    def __call__(self, *args, **kwargs) -> dict:
        return {self.column_name: self._id}

    def __and__(self, other: 'Specification') -> 'SpecificationUnion':
        return SpecificationUnion(self() | other())


class SpecificationUnion(Specification):
    def __init__(self, specification: dict):
        self._union = specification

    def __call__(self) -> dict:
        return self._union


def auto_increment(func):
    setattr(func, 'counter', 0)

    def wrap(*args, **kwargs):
        func.counter += 1
        kwargs['counter'] = func.counter
        return func(*args, **kwargs)

    return wrap


@auto_increment
def specification_fabric(
    view_name: str,
    column_name: str = 'id',
    counter=None,
) -> Specification:
    exec(
        f"""class Specification_{counter}(Specification):
    def __init__(self, {view_name}: int | str = None): 
        self._id = {view_name}
        self.column_name = '{column_name}'
"""
    )
    return locals().get(f'Specification_{counter}')


SessionID = specification_fabric('session_id', 'channel_id')
UserID = specification_fabric('user_id', 'member_id')

Unclosed = specification_fabric('end', 'end')
ActivityID = specification_fabric('app_id', 'app_id')
MessageID = specification_fabric('message_id', 'message_id')
LeaderID = specification_fabric('leader_id', 'leader_id')
ChannelID = specification_fabric('channel_id', 'channel_id')
QueryFilter = specification_fabric('query', 'query')
MusicUserID = specification_fabric('user_id', 'user_id')

ID = specification_fabric('id')
SessionMember = specification_fabric('user_id')
SentMessageID = specification_fabric('message_id')
EmojiID = specification_fabric('emoji_id')
AppID = specification_fabric('app_id')
RoleID = specification_fabric('role_id')
