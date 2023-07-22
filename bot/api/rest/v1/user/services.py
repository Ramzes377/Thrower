from fastapi import Depends
from sqlalchemy import alias
from sqlalchemy.sql import func
from sqlalchemy.sql.elements import BinaryExpression

from .. import tables
from ..base_specification import Specification
from ..dependencies import default_period
from ..schemas import Member, IngameSeconds, DurationActivity
from ..service import CreateReadUpdate
from ...database import Session


class SrvUser(CreateReadUpdate):
    table = tables.Member

    @classmethod
    def filter_by_timeperiod(
            cls,
            period: dict = Depends(default_period)
    ) -> BinaryExpression:

        return tables.Session.begin.between(period['begin'], period['end'])

    def get_sessions(
            self,
            user_id: Specification,
            filters: BinaryExpression = None
    ) -> list[Session]:

        m: Member = self.get(user_id)
        return m.sessions.filter(filters).all()

    def _app_sessions(self, specification: Specification):
        return (
            self._session.query(tables.Activity.id, tables.Activity.member_id,
                                tables.Activity.begin, tables.Activity.end,
                                tables.Activity.duration.label('duration'))
            .filter_by(**specification())
        )

    def user_activities(
            self,
            specification: Specification
    ) -> list[DurationActivity]:

        return self._app_sessions(specification).all()

    def _durations(self, member_id: Specification):

        app_sess = alias(self._app_sessions(member_id))
        return (
            self._session.query(app_sess.c.activity_id.label('app_id'),
                                func.sum(app_sess.c.duration).label('seconds'))
            .group_by(app_sess.c.activity_id, app_sess.c.activity_member_id)
        )

    def durations(self, member_id: Specification) -> list[IngameSeconds]:
        return self._durations(member_id).all()

    def concrete_duration(
            self,
            member_id: Specification,
            role_id: Specification
    ) -> IngameSeconds | None:

        durations = alias(self._durations(member_id))
        return (
            self._session.query(durations)
            .join(tables.Role, tables.Role.app_id == durations.c.app_id)
            .filter_by(**role_id())
            .first()
        )
