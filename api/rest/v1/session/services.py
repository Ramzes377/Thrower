from datetime import datetime

from fastapi import HTTPException, status

from .. import tables
from ..schemas import Session
from ..service import CreateReadUpdate
from ..specifications import Unclosed
from ..base_specification import Specification


class SrvSession(CreateReadUpdate):
    table = tables.Session

    def all(self, begin: datetime, end: datetime) -> list[Session]:
        sessions = super().all()
        return sessions.filter(tables.Session.begin.between(begin, end)).all()

    def _unclosed(self):
        unclosed_specification = Unclosed(None)
        return self._get(unclosed_specification).order_by(tables.Session.begin.desc())

    def unclosed(self) -> list[Session]:
        return self._unclosed().all()

    def user_unclosed(self, leader_id: Specification) -> Session | None:
        return self._unclosed().filter_by(**leader_id()).first()

    def add_member(self, sess_specification: Specification, user_specification: Specification) -> tables.Member:
        user = self._session.query(tables.Member).filter_by(**user_specification()).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        session = self.get(sess_specification)
        session.members.append(user)
        self.create(session)
        return user
