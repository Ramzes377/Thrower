from api.rest.v1.base_specification import BaseSpecification


class EmojiID(BaseSpecification):
    column_name = 'id'

    def __init__(self, emoji_id: int):
        super().__init__(emoji_id)
