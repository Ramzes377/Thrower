from api.rest.v1 import tables
from api.rest.v1.schemas import FavoriteMusic

from api.rest.v1.base_service import BaseService


class SrvFavoriteMusic(BaseService):
    def _get(self, user_id: int):
        return (
            self._session.query(tables.FavoriteMusic)
                .filter_by(user_id=user_id)
                .order_by(tables.FavoriteMusic.counter.desc())
        )

    def get(self, user_id: int) -> list[FavoriteMusic]:
        return self._get(user_id).limit(20).all()

    def _get_record(self, user_id: int, query: str) -> FavoriteMusic:
        return (
            self._get(user_id)
                .filter_by(query=query)
                .first()
        )

    def post(self, data: FavoriteMusic) -> tables.FavoriteMusic:
        record = self._get_record(data.user_id, data.query)
        if record:
            self.edit_object(record, {'counter': record.counter + 1})
            return record

        favorite_music = tables.FavoriteMusic(**data.dict())
        self.add_object(favorite_music)
        return favorite_music
