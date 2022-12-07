from datetime import datetime

from fastapi import HTTPException, status

from api.rest.v1 import tables
from api.rest.v1.schemas import Member, Session, Activity

from api.rest.v1.base_service import BaseService


class SrvUser(BaseService):
    def get_all(self) -> list[Member]:
        users = self._session.query(tables.Member).all()
        return users

    def _get_user(self, user_id: int):
        user = self._session.query(tables.Member).filter_by(id=user_id).first()
        return user

    def get(self, user_id: int) -> Member:
        user = self._get_user(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return user

    def post(self, userdata: Member) -> tables.Member:
        user = tables.Member(**userdata.dict())
        self._db_add_obj(user)
        return user

    def put(self, user_id: int, userdata: Member | dict) -> Member:
        user = self.get(user_id)
        self._db_edit_obj(user, userdata)
        return user

    def get_activities(self, user_id: int) -> list[Activity]:
        user = self.get(user_id)
        return user.activities

    def get_sessions(self, user_id: int, begin: datetime, end: datetime) -> list[Session]:
        return (
            self.get(user_id)
                .sessions
                .filter(tables.Session.begin.between(begin, end))
                .all()
        )