from api.rest.v1 import tables
from api.rest.v1.misc import desqllize, rm_keys
from api.rest.v1.schemas import Leadership

from api.rest.v1.base_service import BaseService


class SrvLeadership(BaseService):
    def _sess_leadership(self, session_id: int):
        leadership = (
            self._session
                .query(tables.Leadership)
                .filter_by(channel_id=session_id)
                .order_by(tables.Leadership.begin.desc())
        )
        return leadership

    def get_all(self, session_id: int) -> list[Leadership]:
        return self._sess_leadership(session_id).all()

    def get_current(self, sess_id: int) -> Leadership:
        return self._sess_leadership(sess_id).limit(1).first()

    def post(self, leadershipdata: Leadership | dict) -> tables.Leadership:
        if isinstance(leadershipdata, Leadership):
            channel_id = leadershipdata.channel_id
            data = leadershipdata.dict()
        else:
            channel_id = leadershipdata['channel_id']
            data = leadershipdata

        current_leader = self.get_current(channel_id)
        if current_leader:
            data = desqllize(leadershipdata)
            new_leader_id = data.pop('member_id')
            self._db_edit_obj(current_leader, data)
            if new_leader_id is None:
                return current_leader
            data['begin'] = data.pop('end')
            data['end'] = None
            data['member_id'] = new_leader_id

        leadership = tables.Leadership(**data)
        self._db_add_obj(leadership)
        return leadership

    def get_by_message(self, msg_id: int) -> list[Leadership]:
        leadership = (
            self._session
                .query(tables.Leadership)
                .join(tables.Session, tables.Session.channel_id == tables.Leadership.channel_id)
                .filter(tables.Session.message_id == msg_id)
                .order_by(tables.Leadership.begin.desc())
                .all()
        )
        return leadership
