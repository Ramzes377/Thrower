from .. import tables
from ..base_specification import Specification
from ..schemas import Leadership, LeaderChange
from ..service import CreateReadUpdate
from ..specifications import SessionID, Unclosed
from ..custom_responses import modify_response


class SrvLeadership(CreateReadUpdate):
    table = tables.Leadership
    order_by = tables.Leadership.begin.desc()  # for ordering in log list

    def get(self, specification: Specification, *_):
        return (
            self._base_query
            .filter_by(**specification())
            .order_by(tables.Leadership.end.desc())
            .first()
        )

    def _end_current_leadership(self, leadership: Leadership | LeaderChange) -> Leadership | None:
        specification = SessionID(leadership.channel_id) & Unclosed()
        _leadership: tables.Leadership = self.get(specification)

        if _leadership is None:
            return

        self.update(_leadership, {'end': leadership.begin})
        return _leadership

    def history(self, specification: Specification) -> list[Leadership]:
        return super().all(query=self._get(specification))

    def post(self, leadership: Leadership | LeaderChange) -> tables.Leadership:
        current = self._end_current_leadership(leadership)

        if leadership.member_id is None and current:  # session is closed
            return modify_response(current)

        response = super().post(leadership)
        if current is not None:     # modify row response
            response = modify_response(response)
        return response
