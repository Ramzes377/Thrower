from fastapi import Depends
from sqlalchemy import select, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from api import tables
from api.specification import Specification
from api.schemas import Prescence, EndPrescence
from api.service import CreateReadUpdate
from api.specification import SessionID, UserID, Unclosed
from api.database import get_session


class SrvPrescence(CreateReadUpdate):
    table = tables.Prescence
    order_by = table.begin

    def __init__(self, session: AsyncSession = Depends(get_session)):
        super().__init__(session)
        # override base query to use base method _get  more native way with filter by message_id
        self._base_query = self._base_query.join(tables.Session)

    async def get(self, specification: Specification, *args) -> Sequence:
        prescences = await self._session.scalars(self._get(specification))
        return prescences.all()

    async def _member_prescence(self, specification: Specification) -> Prescence:
        member_prescence = await self._session.scalars(
            select(tables.Prescence)
            .filter_by(**specification())
            .order_by(tables.Prescence.begin.desc())
        )
        return member_prescence.first()

    async def patch(self, prescence: EndPrescence, *args) -> Prescence:
        specification = (SessionID(prescence.channel_id) &
                         UserID(prescence.member_id) & Unclosed())
        return await super().patch(
            specification,
            prescence,
            get_method=self._member_prescence
        )
