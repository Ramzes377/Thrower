from sqlalchemy import update

from src.app import tables
from src.app.schemas import FavoriteMusic
from src.app.service import CreateReadUpdate
from src.app.specification import MusicUserID, QueryFilter, Specification


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

    async def post(self, music_data: FavoriteMusic, *_) -> dict:
        specification = MusicUserID(music_data.user_id) & QueryFilter(
            music_data.query)
        stmt = (
                update(self.table)
                .filter_by(**specification())
                .values(counter=self.table.counter + 1)
                .returning(self.table.counter)
            )

        async with self._session.begin():
            r = await self._session.execute(stmt)
            if (counter := r.scalars().first()) is not None:
                return {'user_id': music_data.user_id,
                        'query': music_data.query,
                        'counter': counter}

        return await super().post(music_data)
