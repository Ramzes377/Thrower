from api.rest.v1.base_specification import BaseSpecification


class UserID(BaseSpecification):
    column_name = 'user_id'

    def __init__(self, user_id: int):
        super().__init__(user_id)


class QueryFilter(BaseSpecification):
    column_name = 'query'

    def __init__(self, query: int):
        super().__init__(query)
