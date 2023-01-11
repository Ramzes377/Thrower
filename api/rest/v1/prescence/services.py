from api.rest.v1 import tables
from ..misc import desqllize
from ..service import CreateReadUpdate
from ..schemas import Prescence
from ..base_specification import Specification
from ..specifications import SessionID, UserID, Unclosed


def unsclosed_user_session(channel_id: int, member_id: int):
    return SessionID(channel_id) & UserID(member_id) & Unclosed(None)


class SrvPrescence(CreateReadUpdate):
    table = tables.Prescence

    def get(self, specification: Specification) -> list[Prescence]:
        return (
            self._base_query
            .join(tables.Session, tables.Session.channel_id == self.table.channel_id)
            .filter_by(**specification())
            .order_by(self.table.begin)
            .all()
        )

    def _member_prescence(self, specification: Specification) -> Prescence:
        return (
            self._session.query(tables.Prescence)
            .filter_by(**specification())
            .order_by(tables.Prescence.begin.desc())
            .first()
        )

    def post(self, prescence: Prescence) -> tables.Prescence:
        channel_id, member_id = prescence.channel_id, prescence.member_id
        specification = unsclosed_user_session(channel_id, member_id)
        member_prescence = self._member_prescence(specification)
        if member_prescence:  # trying to add member that's prescence isn't closed
            self.update(member_prescence, prescence)
            return member_prescence
        prescence = tables.Prescence(**prescence.dict())  # type: ignore
        self.create(prescence)
        return prescence

    def patch(self, prescence: Prescence | dict, *args) -> Prescence:
        channel_id, member_id = prescence['channel_id'], prescence['member_id']
        specification = unsclosed_user_session(channel_id, member_id)
        member_prescence = self._member_prescence(specification)
        self.update(member_prescence, desqllize(prescence))
        return member_prescence
