from fastapi import Depends

from api.rest.database import Session, get_session
from api.rest.v1.base_specification import Specification


class BaseService:
    table = None

    def __init__(self, session: Session = Depends(get_session)):
        self._session = session
        self._base_query = self._session.query(self.table)


class Create(BaseService):
    def create(self, obj):
        try:
            self._session.add(obj)
            self._session.commit()
        except:
            self._session.rollback()

    def post(self, data: BaseService):
        obj = self.table(**data.dict())  # type: ignore
        self.create(obj)
        return obj


class Read(BaseService):
    def _get(self, specification: Specification):
        return self._base_query.filter_by(**specification())

    def get(self, specification: Specification):
        return self._get(specification).first()

    def all(self, *args, **kwargs):
        return self._base_query


class Update(Read):
    def update(self, obj, data):
        if not obj:
            return
        iterable = data.items() if isinstance(data, dict) else data
        for k, v in iterable:
            setattr(obj, k, v)
        self._session.commit()

    def patch(self, specification: Specification, data: BaseService, *args, **kwargs) -> BaseService:
        obj = self.get(specification)
        self.update(obj, data)
        return obj


class Delete(Read):
    def delete(self, role_id: int):
        role = self.get(role_id)
        self._session.delete(role)
        self._session.commit()
        return {"ok": True}


class CreateRead(Create, Read):
    pass


class CreateReadUpdate(Update, CreateRead):
    pass


class CRUD(Delete, CreateReadUpdate):
    pass
