from api.rest.v1 import tables
from api.rest.v1.base_specification import Specification
from api.rest.v1.misc import desqllize
from api.rest.v1.schemas import Leadership
from api.rest.v1.service import CreateReadUpdate

from ..specifications import SessionID


class SrvLeadership(CreateReadUpdate):
    table = tables.Leadership

    def _get(self, specification: Specification):
        return (
            self._session.query(tables.Leadership)
            .join(tables.Session, tables.Session.channel_id == tables.Leadership.channel_id)
            .filter_by(**specification())
            .order_by(tables.Leadership.begin.desc())
        )

    def get(self, specification: Specification) -> list[Leadership]:
        return self._get(specification).all()

    def post(self, leadership: Leadership | dict) -> tables.Leadership:
        if isinstance(leadership, Leadership):
            channel_id = leadership.channel_id
            data = leadership.dict()
        else:
            channel_id = leadership['channel_id']
            data = leadership

        specification = SessionID(channel_id)
        current_leader = self.current(specification)
        if current_leader:
            data = desqllize(leadership)
            new_leader_id = data.pop('member_id')
            self.update(current_leader, data)
            if new_leader_id is None:
                return current_leader
            data['begin'] = data.pop('end')
            data['end'] = None
            data['member_id'] = new_leader_id

        leadership = tables.Leadership(**data)  # type: ignore
        self.create(leadership)
        return leadership

    def current(self, session_id: Specification) -> Leadership:
        return self._get(session_id).first()
