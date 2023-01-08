from fastapi import HTTPException, status

from api.rest.v1 import tables
from api.rest.v1.misc import desqllize
from api.rest.v1.base_service import BaseService
from api.rest.v1.schemas import Prescence


class SrvPrescence(BaseService):
    def get(self, channel_id: int = None, message_id: int = None) -> list[Prescence]:
        prescences = None

        if channel_id is not None:
            prescences = self._session.query(tables.Prescence).filter_by(channel_id=channel_id).all()
        if message_id is not None:
            prescences = (
                self._session.query(tables.Prescence)
                .join(tables.Session, tables.Session.channel_id == tables.Prescence.channel_id)
                .filter_by(message_id=message_id)
                .order_by(tables.Prescence.begin)
                .all()
            )

        if not prescences:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return prescences

    def _member_prescence(self, channel_id: int, member_id: int) -> Prescence:
        return (
            self._session.query(tables.Prescence)
            .filter_by(channel_id=channel_id,
                       member_id=member_id)
            .filter_by(end=None)
            .order_by(tables.Prescence.begin.desc())
            .first()
        )

    def post(self, prescencedata: Prescence) -> tables.Prescence:
        channel_id, member_id = prescencedata.channel_id, prescencedata.member_id
        member_prescence = self._member_prescence(channel_id, member_id)
        if member_prescence:  # trying to add member that's prescence isn't closed
            self.edit_object(member_prescence, prescencedata)
            return member_prescence
        prescence = tables.Prescence(**prescencedata.dict())  # type: ignore
        self.add_object(prescence)
        return prescence

    def put(self, prescencedata: Prescence | dict) -> Prescence:
        channel_id, member_id = prescencedata['channel_id'], prescencedata['member_id']
        member_prescence = self._member_prescence(channel_id, member_id)
        self.edit_object(member_prescence, desqllize(prescencedata))
        return member_prescence