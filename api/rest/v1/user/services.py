from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import alias, and_
from sqlalchemy.sql import func

from api.rest.v1 import tables
from api.rest.v1.schemas import Member, Session, IngameSeconds, DurationActivity
from api.rest.v1.base_service import BaseService


class SrvUser(BaseService):
    def all(self) -> list[Member]:
        users = self._session.query(tables.Member).all()
        return users

    def get(self, user_id: int) -> Member:
        user = self._session.query(tables.Member).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return user

    def post(self, userdata: Member) -> tables.Member:
        user = tables.Member(**userdata.dict())
        self.add_object(user)
        return user

    def put(self, user_id: int, userdata: Member | dict) -> Member:
        user = self.get(user_id)
        self.edit_object(user, userdata)
        return user

    def get_sessions(self, user_id: int, begin: datetime, end: datetime) -> list[Session]:
        return (
            self.get(user_id).sessions
            .filter(tables.Session.begin.between(begin, end))
            .all()
        )

    def _app_sessions(self, user_id: int):
        return (
            self._session.query(
                tables.Activity.id,
                tables.Activity.member_id,
                tables.Activity.begin,
                tables.Activity.end,
                tables.Activity.duration
            )
            .select_from(tables.Activity)
            .filter_by(member_id=user_id)
        )

    def app_sessions(self, user_id: int) -> list[DurationActivity]:
        return self._app_sessions(user_id).all()

    def concrete_app_sessions(self, user_id: int, app_id: int) -> list[DurationActivity]:
        return self._app_sessions(user_id).filter_by(id=app_id).all()

    def _durations(self, user_id: int):
        app_sess = alias(self._app_sessions(user_id))
        return (
            self._session.query(
                app_sess.c.activity_id.label('app_id'),
                func.sum(app_sess.c.duration).label('seconds')
            )
            .select_from(app_sess)
            .group_by(app_sess.c.activity_id, app_sess.c.activity_member_id)
        )

    def durations(self, user_id: int) -> list[IngameSeconds]:
        return self._durations(user_id).all()

    def concrete_duration(self, user_id: int, role_id: int) -> IngameSeconds:
        durations = alias(self._durations(user_id))
        return (
            self._session.query(durations)
            .join(tables.Role, and_(tables.Role.id == role_id, tables.Role.app_id == durations.c.app_id))
            .first()
        )
