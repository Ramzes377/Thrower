from api.rest.v1.base_specification import BaseSpecification


class UserID(BaseSpecification):
    column_name = 'id'

    def __init__(self, user_id: int):
        super().__init__(user_id)
