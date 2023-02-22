from fastapi import HTTPException, status, Depends
from sqlalchemy.sql.elements import BinaryExpression

from .. import tables
from ..base_specification import Specification
from ..dependencies import default_period
from ..schemas import Session
from ..service import CreateReadUpdate
from ..specifications import Unclosed


class SrvSession(CreateReadUpdate):
    table = tables.Session
    order_by = tables.Session.begin

    @classmethod
    def filter_by_timeperiod(cls, period: dict = Depends(default_period)) -> BinaryExpression:
        return cls.table.begin.between(period['begin'], period['end'])

    def _unclosed(self):
        unclosed_specification = Unclosed()
        return self._base_query.filter_by(**unclosed_specification()).order_by(tables.Session.begin.desc())

    def unclosed(self) -> list[Session]:
        return self._unclosed().all()

    def user_unclosed(self, leader_id: Specification) -> Session | None:
        return self._unclosed().filter_by(**leader_id()).first()

    def add_member(self, sess_specification: Specification, user_specification: Specification) -> tables.Member:
        user = self._session.query(tables.Member).filter_by(**user_specification()).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        session: tables.Session = self.get(sess_specification)
        session.members.append(user)
        self.create(session)
        return user
