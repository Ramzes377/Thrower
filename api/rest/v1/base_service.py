from fastapi import Depends
from api.rest.database import Session, get_session


class BaseService:
    def __init__(self, session: Session = Depends(get_session)):
        self._session = session

    def get(self, *args, **kwargs):
        raise NotImplementedError

    def post(self, *args, **kwargs):
        raise NotImplementedError

    def put(self, *args, **kwargs):
        raise NotImplementedError

    def add_object(self, obj):
        try:
            self._session.add(obj)
            self._session.commit()
        except:
            self._session.rollback()

    def edit_object(self, obj, data):
        if not obj:
            return
        iterable = data.items() if isinstance(data, dict) else data
        for k, v in iterable:
            setattr(obj, k, v)
        self._session.commit()
