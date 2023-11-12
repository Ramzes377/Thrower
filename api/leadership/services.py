from sqlalchemy import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from api import tables
from api.specification import Specification
from api.tables import Base as BaseTable
from api.schemas import Leadership, LeaderChange
from api.service import CreateReadUpdate
from api.specification import SessionID, Unclosed
from utils import table_to_json


class SrvLeadership(CreateReadUpdate):
    table = tables.Leadership
    order_by = tables.Leadership.begin.desc()  # for ordering in log list

    async def get(self,
                  specification: Specification = None,
                  session_: AsyncSession = None,
                  suppress_error: bool = False,
                  **additional_filters) -> BaseTable:

        return await super().get(specification,
                                 session_=session_,
                                 _ordering=tables.Leadership.end.desc(),
                                 suppress_error=True)

    async def _end_current_leadership(
            self,
            leadership: Leadership | LeaderChange
    ) -> Leadership | None:
        """ End current leadership of session."""

        specification = SessionID(leadership.channel_id) & Unclosed()

        if (_leadership := await self.get(specification)) is not None:
            return await super().patch(
                specification,
                {'end': leadership.begin},
                get_method=self.get
            )

    async def history(self, specification: Specification) -> Sequence:
        return await super().all(query=self.query(specification))

    async def post(
            self,
            leadership: Leadership | LeaderChange,
            repeat_on_failure: bool = True,
    ) -> tables.Leadership | JSONResponse:
        """
        Set previous leadership as finished if exist
        and creates new leadership of session.
        """

        current = await self._end_current_leadership(leadership)

        if current and leadership.member_id is None:  # session is closed
            return JSONResponse(status_code=202, content=table_to_json(current))

        _leadership = await super().post(leadership, repeat_on_failure)
        if current is not None:  # session not over and leader change
            return JSONResponse(status_code=202,
                                content=table_to_json(_leadership))

        return _leadership
