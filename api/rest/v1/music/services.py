from .. import tables
from .specifications import UserID, QueryFilter
from ..schemas import FavoriteMusic
from ..service import CreateReadUpdate
from ..base_specification import Specification


class SrvFavoriteMusic(CreateReadUpdate):
    table = tables.FavoriteMusic
    order_by = table.counter.desc()

    def get(self, user_id: Specification, amount: int, *args) -> list[FavoriteMusic]:
        return self._get(user_id).limit(amount).all()

    def _get_record(self, user_id: int, query: str) -> FavoriteMusic:
        specification = UserID(user_id) & QueryFilter(query)
        return self._get(specification).first()

    def post(self, data: FavoriteMusic) -> tables.FavoriteMusic:
        record = self._get_record(data.user_id, data.query)
        if record:  # track already exists, just increasing it counter
            self.update(record, {'counter': record.counter + 1})
            return record

        favorite_music = tables.FavoriteMusic(**data.dict())
        self.create(favorite_music)
        return favorite_music
