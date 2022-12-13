from fastapi import HTTPException, status
from sqlalchemy import or_

from api.rest.v1 import tables
from api.rest.v1.base_service import BaseService
from api.rest.v1.schemas import Member, Session, Activity, Prescence, Leadership


class SrvSession(BaseService):
    def _get(self, channel_id: int) -> Session:
        session = self._session.query(tables.Session).filter_by(channel_id=channel_id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return session

    def _get_sessions(self):
        return self._session.query(tables.Session)

    def get_all(self) -> list[Session]:
        return self._get_sessions().all()

    def _unclosed(self):
        return (
            self._get_sessions()
                .filter_by(end=None)
                .order_by(tables.Session.begin.desc())
        )

    def get_unclosed(self):
        return self._unclosed().all()

    def get(self, channel_id: int) -> Session:
        return self._get(channel_id)

    def get_by_msgid(self, message_id: int) -> Session:
        session = self._session.query(tables.Session).filter_by(message_id=message_id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return session

    def get_by_leader(self, leader_id: int) -> Session:
        session = self._unclosed().filter_by(leader_id=leader_id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return session

    def post(self, sessdata: Session, *args, **kwargs) -> tables.Session:
        sess = tables.Session(**sessdata.dict())
        self._db_add_obj(sess)
        return sess

    def put(self, channel_id: int, sessdata: Session) -> Session:
        session = self._get(channel_id)
        self._db_edit_obj(session, sessdata)
        return session

    def get_prescence(self, channel_id: int) -> list[Prescence]:
        session = self.get(channel_id)
        return session.prescence

    def get_members(self, channel_id: int) -> list[Member]:
        session = self.get(channel_id)
        return session.members.all()

    def add_member(self, channel_id: int, user_id: int) -> tables.Member:
        user = self._session.query(tables.Member).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        session = self.get(channel_id)
        session.members.append(user)
        self._db_add_obj(session)
        return user

    def get_leadership(self, message_id: int) -> list[Leadership]:
        session = self.get_by_msgid(message_id)
        return session.leadership

    def _activities(self):
        return (
            self._session.query(tables.Activity)
                .join(tables.Member)
                .join(tables.Session, tables.Member.sessions)
                .filter(tables.Session.begin <= tables.Activity.begin,
                        or_(tables.Session.end == None, tables.Session.end >= tables.Activity.end))
                # activity "inside" session
                .join(tables.Prescence, tables.Session.channel_id.label("sess_id"))  # get all session prescence
                .filter(tables.Member.id == tables.Prescence.member_id)
                .filter(tables.Prescence.begin <= tables.Activity.begin,
                        or_(tables.Prescence.end == None, tables.Prescence.end >= tables.Activity.end))
                # fetch only activity that "inside" prescence
                .order_by(tables.Activity.begin)
        )

    def get_activities(self, channel_id: int) -> list[Activity]:
        return self._activities().filter_by(channel_id=channel_id).all()

    def get_activities_by_msg(self, msg_id: int) -> list[Activity]:
        return self._activities().filter(tables.Session.message_id == msg_id).all()
