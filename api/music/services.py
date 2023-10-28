from sqlalchemy import Sequence

from api.specification import MusicUserID, QueryFilter
from api import tables
from api.specification import Specification
from api.responses import modify_response
from api.schemas import FavoriteMusic
from api.service import CreateReadUpdate, Service


class SrvFavoriteMusic(CreateReadUpdate):
    table = tables.FavoriteMusic
    order_by = table.counter.desc()

    async def get(
        self,
        user_id: Specification = None,
        amount: int = None,
        *args,
    ) -> Sequence:
        records = await self._session.scalars(self._get(user_id).limit(amount))
        return records.all()

    async def _get_record(self, user_id: int, query: str) -> FavoriteMusic:
        specification = MusicUserID(user_id) & QueryFilter(query)
        record = await self._session.scalars(self._get(specification))
        return record.first()

    async def post(self, music_data: FavoriteMusic) -> tables.FavoriteMusic:
        record = await self._get_record(music_data.user_id, music_data.query)
        if record:  # track already exists, just increasing it counter
            await self.update(record, {'counter': record.counter + 1})
            return modify_response(record)
        return await super().post(music_data)
