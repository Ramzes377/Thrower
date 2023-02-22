from .specifications import UserID, QueryFilter
from .. import tables
from ..base_specification import Specification
from ..custom_responses import modify_response
from ..schemas import FavoriteMusic
from ..service import CreateReadUpdate


class SrvFavoriteMusic(CreateReadUpdate):
    table = tables.FavoriteMusic
    order_by = table.counter.desc()

    def get(self, user_id: Specification, amount: int, *args) -> list[FavoriteMusic]:
        return self._get(user_id).limit(amount).all()

    def _get_record(self, user_id: int, query: str) -> FavoriteMusic:
        specification = UserID(user_id) & QueryFilter(query)
        return self._get(specification).first()

    def post(self, music_data: FavoriteMusic) -> tables.FavoriteMusic:
        record = self._get_record(music_data.user_id, music_data.query)
        if record:  # track already exists, just increasing it counter
            self.update(record, {'counter': record.counter + 1})
            return modify_response(record)
        return super().post(music_data)
