from abc import abstractmethod

import sqlalchemy.exc
from fastapi import Depends
from api.rest.database import Session, get_session


class BaseService:
    def __init__(self, session: Session = Depends(get_session)):
        self._session = session

    @abstractmethod
    def get(self, *args, **kwargs):
        pass

    @abstractmethod
    def post(self, *args, **kwargs):
        pass

    @abstractmethod
    def put(self, *args, **kwargs):
        pass

    def _db_add_obj(self, obj):
        try:
            self._session.add(obj)
            self._session.commit()
        except sqlalchemy.exc.IntegrityError:   # object already exist
            pass

    def _db_edit_obj(self, obj, data):
        if not obj:
            return
        iterable = data.items() if isinstance(data, dict) else data
        for k, v in iterable:
            setattr(obj, k, v)
        self._session.commit()
