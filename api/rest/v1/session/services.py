from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import or_, and_, func

from api.rest.v1 import tables
from api.rest.v1.base_service import BaseService
from api.rest.v1.schemas import Member, Session, Activity, Prescence, Leadership


class SrvSession(BaseService):

    def get(self, channel_id: int = None, leader_id: int = None, message_id: int = None) -> Session:
        session = None

        if channel_id is not None:
            session = self._session.query(tables.Session).filter_by(channel_id=channel_id).first()
        elif message_id is not None:
            session = self._session.query(tables.Session).filter_by(message_id=message_id).first()
        elif leader_id is not None:
            session = self._unclosed().filter_by(leader_id=leader_id).first()

        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return session

    def post(self, sessdata: Session, *args, **kwargs) -> tables.Session:
        sess = tables.Session(**sessdata.dict())  # type: ignore
        self.add_object(sess)
        return sess

    def put(self, channel_id: int, sessdata: Session) -> Session:
        session = self.get(channel_id=channel_id)
        self.edit_object(session, sessdata)
        return session

    def all(self, begin: datetime, end: datetime) -> list[Session]:
        return (
            self._session.query(tables.Session)
            .filter(tables.Session.begin.between(begin, end))
            .all()
        )

    def unclosed(self):
        return self._unclosed().all()

    def prescence(self, channel_id: int) -> list[Prescence]:
        session = self.get(channel_id)
        return session.prescence

    def members(self, channel_id: int) -> list[Member]:
        session = self.get(channel_id)
        return session.members.all()

    def leadership(self, message_id: int) -> list[Leadership]:
        session = self.get(message_id=message_id)
        return session.leadership

    def activities(self, channel_id: int) -> list[Activity]:
        return self._activities().filter_by(channel_id=channel_id).all()

    def activities_by_msg(self, message_id: int) -> list[Activity]:
        return self._activities().filter(tables.Session.message_id == message_id).all()

    def add_member(self, channel_id: int, user_id: int) -> tables.Member:
        user = self._session.query(tables.Member).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        session = self.get(channel_id)
        session.members.append(user)
        self.add_object(session)
        return user

    def _unclosed(self):
        return (
            self._session.query(tables.Session)
            .filter_by(end=None)
            .order_by(tables.Session.begin.desc())
        )

    def _activities(self):
        # prescence during begin or end of activity
        return (
            self._session.query(tables.Activity)
            .join(tables.Member)
            .join(tables.Session, tables.Member.sessions)
            .join(tables.Prescence,
                  and_(tables.Prescence.member_id == tables.Member.id,
                       tables.Prescence.channel_id == tables.Session.channel_id,
                       or_(tables.Activity.begin.between(tables.Prescence.begin,
                                                         func.coalesce(tables.Prescence.end, func.date('now',
                                                                                                       'start of month',
                                                                                                       '+1 month'))),
                           tables.Activity.end.between(tables.Prescence.begin,
                                                       func.coalesce(tables.Prescence.end, func.date('now',
                                                                                                     'start of month',
                                                                                                     '+1 month'))))))
            .order_by(tables.Activity.begin)
        )
