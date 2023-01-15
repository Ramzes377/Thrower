from api.rest.v1.base_specification import specification_fabric, BaseSpecification

ID = specification_fabric('id')
Unclosed = specification_fabric('end')


class SessionID(BaseSpecification):
    column_name = 'channel_id'

    def __init__(self, session_id: int):
        super().__init__(session_id)


class ActivityID(BaseSpecification):
    column_name = 'app_id'

    def __init__(self, app_id: int):
        super().__init__(app_id)


class UserID(BaseSpecification):
    column_name = 'member_id'

    def __init__(self, user_id: int):
        super().__init__(user_id)


class RoleID(BaseSpecification):
    column_name = 'id'

    def __init__(self, role_id: int):
        super().__init__(role_id)


class MessageID(BaseSpecification):
    column_name = 'message_id'

    def __init__(self, message_id: int):
        super().__init__(message_id)


class AppID(BaseSpecification):
    column_name = 'id'

    def __init__(self, app_id: int):
        super().__init__(app_id)



