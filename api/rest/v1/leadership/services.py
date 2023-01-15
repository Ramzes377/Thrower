from fastapi import Depends

from .. import tables
from ..base_specification import Specification
from ..schemas import Leadership, LeaderChange
from ..service import CreateReadUpdate
from ..specifications import SessionID
from ...database import Session, get_session


class SrvLeadership(CreateReadUpdate):
    table = tables.Leadership
    order_by = tables.Leadership.begin.desc()

    def __init__(self, session: Session = Depends(get_session)):
        super().__init__(session)
        self._base_query = self._base_query.join(tables.Session)

    def _end_current_leadership(self, leadership: Leadership | LeaderChange) -> Leadership | None:
        specification = SessionID(leadership.channel_id)
        session_leader: tables.Leadership = self.get(specification)

        if session_leader is None:
            return

        self.update(session_leader, {'end': leadership.begin})
        return session_leader

    def history(self, specification: Specification) -> list[Leadership]:
        return super().all(query=self._get(specification))

    def post(self, leadership: Leadership | LeaderChange) -> tables.Leadership:
        current = self._end_current_leadership(leadership)
        if current and leadership.member_id is None:  # session is closed
            return current
        return super().post(leadership)
