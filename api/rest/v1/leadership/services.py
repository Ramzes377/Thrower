from sqlalchemy import and_
from fastapi import HTTPException, status

from api.rest.v1 import tables
from api.rest.v1.misc import desqllize
from api.rest.v1.schemas import Leadership

from api.rest.v1.base_service import BaseService


class SrvLeadership(BaseService):
    def _sess_leadership(self, session_id: int = None, message_id: int = None):
        leadership = None

        if session_id is not None:
            leadership = (self._session.query(tables.Leadership)
                          .filter_by(channel_id=session_id)
                          .order_by(tables.Leadership.begin.desc()))
        elif message_id is not None:
            leadership = (self._session.query(tables.Leadership)
                          .join(tables.Session, and_(tables.Session.channel_id == tables.Leadership.channel_id,
                                                     tables.Session.message_id == message_id))
                          .order_by(tables.Leadership.begin.desc()))

        if not leadership:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return leadership

    def get(self, session_id: int = None, message_id: int = None) -> list[Leadership]:
        return self._sess_leadership(session_id, message_id).all()

    def post(self, leadership_data: Leadership | dict) -> tables.Leadership:
        if isinstance(leadership_data, Leadership):
            channel_id = leadership_data.channel_id
            data = leadership_data.dict()
        else:
            channel_id = leadership_data['channel_id']
            data = leadership_data

        current_leader = self.current(channel_id)
        if current_leader:
            data = desqllize(leadership_data)
            new_leader_id = data.pop('member_id')
            self.edit_object(current_leader, data)
            if new_leader_id is None:
                return current_leader
            data['begin'] = data.pop('end')
            data['end'] = None
            data['member_id'] = new_leader_id

        leadership = tables.Leadership(**data)  # type: ignore
        self.add_object(leadership)
        return leadership

    def current(self, session_id: int) -> Leadership:
        return self._sess_leadership(session_id).limit(1).first()