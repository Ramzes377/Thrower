from api.rest.v1.base_specification import BaseSpecification


class LeaderID(BaseSpecification):
    column_name = 'leader_id'

    def __init__(self, leader_id: int):
        super().__init__(leader_id)
