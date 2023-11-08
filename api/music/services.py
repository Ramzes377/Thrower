from contextlib import suppress

from fastapi import HTTPException

from api.specification import MusicUserID, QueryFilter
from api import tables
from api.specification import Specification
from api.schemas import FavoriteMusic
from api.service import CreateReadUpdate


class SrvFavoriteMusic(CreateReadUpdate):
    table = tables.FavoriteMusic
    order_by = table.counter.desc()

    async def first_of_all(
            self,
            user_id: Specification = None,
            amount: int = None
    ):
        records = await self._session.scalars(self.query(user_id).limit(amount))
        return records.all()

    async def post(self, music_data: FavoriteMusic) -> tables.FavoriteMusic:
        specification = MusicUserID(music_data.user_id) & QueryFilter(
            music_data.query)

        with suppress(HTTPException):
            record = await self.get(specification)
            # track already exists, just increasing it counter
            modified_record = await self.patch(
                specification,
                {'counter': record.counter + 1},
                suppress_error=True
            )
            return modified_record

        return await super().post(music_data)
