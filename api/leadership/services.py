from sqlalchemy import Sequence

from api import tables
from api.specification import Specification
from api.responses import modify_response
from api.schemas import Leadership, LeaderChange
from api.service import CreateReadUpdate
from api.specification import SessionID, Unclosed


class SrvLeadership(CreateReadUpdate):
    table = tables.Leadership
    order_by = tables.Leadership.begin.desc()  # for ordering in log list

    async def get(self, specification: Specification, *_):
        leadership = await self._session.scalars(
            self._base_query
            .filter_by(**specification())
            .order_by(tables.Leadership.end.desc())
        )
        return leadership.first()

    async def _end_current_leadership(
        self,
        leadership: Leadership | LeaderChange
    ) -> Leadership | None:
        specification = SessionID(leadership.channel_id) & Unclosed()
        _leadership: tables.Leadership = await self.get(specification)

        if _leadership is None:
            return

        await self.update(_leadership, {'end': leadership.begin})
        return _leadership

    async def history(self, specification: Specification) -> Sequence:
        return await super().all(query=self._get(specification))

    async def post(
        self,
        leadership: Leadership | LeaderChange
    ) -> tables.Leadership:
        current = await self._end_current_leadership(leadership)

        if leadership.member_id is None and current:  # session is closed
            return modify_response(current)

        response = await super().post(leadership)
        if current is not None:  # modify row response
            response = modify_response(response)
        return response
