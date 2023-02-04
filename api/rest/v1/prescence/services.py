from fastapi import Depends

from .. import tables
from ..service import CreateReadUpdate
from ..schemas import Prescence, EndPrescence
from ..base_specification import Specification
from ..specifications import SessionID, UserID, Unclosed
from ...database import Session, get_session


class SrvPrescence(CreateReadUpdate):
    table = tables.Prescence
    order_by = table.begin

    def __init__(self, session: Session = Depends(get_session)):
        super().__init__(session)
        # override base query to use base method _get  more native way with filter by message_id
        self._base_query = self._base_query.join(tables.Session)

    def get(self, specification: Specification, *args) -> list[Prescence]:
        return self._get(specification).all()

    def _member_prescence(self, specification: Specification) -> Prescence:
        return (
            self._session.query(tables.Prescence)
            .filter_by(**specification())
            .order_by(tables.Prescence.begin.desc())
            .first()
        )

    def patch(self, prescence: EndPrescence, *args) -> Prescence:
        specification = SessionID(prescence.channel_id) & UserID(prescence.member_id) & Unclosed()
        return super().patch(specification, prescence, get_method=self._member_prescence)
