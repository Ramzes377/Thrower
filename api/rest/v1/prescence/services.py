from fastapi import HTTPException, status

from api.rest.v1 import tables
from api.rest.v1.misc import desqllize
from api.rest.v1.base_service import BaseService
from api.rest.v1.schemas import Prescence


class SrvPrescence(BaseService):
    def _get(self, channel_id: int) -> list[Prescence]:
        prescences = self._session.query(tables.Prescence).filter_by(channel_id=channel_id).all()
        if not prescences:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return prescences

    def get(self, channel_id: int) -> list[Prescence]:
        return self._get(channel_id)

    def _member_prescence(self, channel_id: int, member_id: int) -> Prescence:
        member_prescence = (
            self._session
                .query(tables.Prescence)
                .filter_by(channel_id=channel_id,
                           member_id=member_id)
                .filter_by(end=None)
                .order_by(tables.Prescence.begin.desc())
                .first()
        )
        return member_prescence

    def post(self, prescencedata: Prescence) -> tables.Prescence:
        channel_id, member_id = prescencedata['channel_id'], prescencedata['member_id']
        member_prescence = self._member_prescence(channel_id, member_id)
        if member_prescence:    # trying to add member that's prescence isn't closed
            return member_prescence
        prescence = tables.Prescence(**prescencedata.dict())
        try:
            self._db_add_obj(prescence)
            return prescence
        finally:
            return

    def put(self, prescencedata: Prescence | dict) -> Prescence:
        channel_id, member_id = prescencedata['channel_id'], prescencedata['member_id']
        member_prescence = self._member_prescence(channel_id, member_id)
        self._db_edit_obj(member_prescence, desqllize(prescencedata))
        return member_prescence

    def get_by_msg(self, message_id: int) -> list[Prescence]:
        return (
            self._session
                .query(tables.Prescence)
                .join(tables.Session)
                .filter(tables.Prescence.channel_id == tables.Session.channel_id)
                .filter_by(message_id=message_id)
                .order_by(tables.Prescence.begin)
                .all()
        )
