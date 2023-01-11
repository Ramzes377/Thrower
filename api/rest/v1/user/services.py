from datetime import datetime

from sqlalchemy import alias
from sqlalchemy.sql import func

from api.rest.database import Session
from api.rest.v1 import tables
from api.rest.v1.base_specification import Specification
from api.rest.v1.schemas import Member, IngameSeconds, DurationActivity
from api.rest.v1.service import CreateReadUpdate


class SrvUser(CreateReadUpdate):
    table = tables.Member

    def all(self) -> list[Member]:
        return super().all().all()

    def get_sessions(self, user_id: Specification, begin: datetime, end: datetime) -> list[Session]:
        return self.get(user_id).sessions.filter(tables.Session.begin.between(begin, end)).all()

    def _app_sessions(self, specification: Specification):
        return self._session.query(tables.Activity, tables.Activity.duration).filter_by(**specification())

    def user_activities(self, specification: Specification) -> list[DurationActivity]:
        return self._app_sessions(specification).all()

    def concrete_user_activity(self, specification: Specification) -> list[DurationActivity]:
        return self._app_sessions(specification).all()

    def _durations(self, member_id: Specification):
        app_sess = alias(self._app_sessions(member_id))
        return (
            self._session.query(app_sess.c.activity_id.label('app_id'), func.sum(app_sess.c.duration).label('seconds'))
            .select_from(app_sess)
            .group_by(app_sess.c.activity_id, app_sess.c.activity_member_id)
        )

    def durations(self, member_id: Specification) -> list[IngameSeconds]:
        return self._durations(member_id).all()

    def concrete_duration(self, member_id: Specification, role_id: Specification) -> IngameSeconds:
        durations = alias(self._durations(member_id))
        return (
            self._session.query(durations)
            .join(tables.Role, tables.Role.app_id == durations.c.app_id)
            .filter_by(**role_id())
            .first()
        )
