from typing import Callable, Any

from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Query
from sqlalchemy.sql.elements import BinaryExpression

from .tables import Base as BaseTable
from .base_specification import Specification
from ..database import Session, get_session


class BaseService:
    table = None
    order_by = None

    def __init__(self, session: Session = Depends(get_session)):
        self._session = session
        self._base_query = self._session.query(self.table)
        self._order_by = self.order_by


class Create(BaseService):
    def create(self, obj: BaseModel) -> None:
        try:
            self._session.add(obj)
            self._session.commit()
        except Exception as e:
            self._session.rollback()
            raise e

    def post(self, data: BaseModel) -> BaseTable:
        obj = self.table(**data.dict())
        self.create(obj)
        return obj


class Read(BaseService):
    @property
    def _query(self) -> Query:
        query = self._base_query
        if self._order_by is not None:
            query = query.order_by(self._order_by)
        return query

    def _get(self, specification: Specification) -> Query:
        return self._query.filter_by(**specification())

    def get(self, specification: Specification, *args: Any, **kwargs: Any) -> BaseTable:
        return self._get(specification).first()

    def all(self, filters: BinaryExpression = None, *args, query: Query | None = None, **kwargs) -> list[BaseTable]:
        query = self._query if query is None else query
        if filters is not None:
            query = query.filter(filters)
        return query.all()


class Update(Read):
    def update(self, obj: BaseService, data: BaseModel | dict) -> None:
        try:
            iterable = data.items() if isinstance(data, dict) else data
            for k, v in iterable:
                setattr(obj, k, v)
            self._session.commit()
        except Exception as e:
            self._session.rollback()
            raise e

    def patch(
            self,
            specification: Specification,
            data: BaseModel | dict,
            *args,
            get_method: Callable = None,
            **kwargs
    ) -> BaseTable:
        get = self.get if get_method is None else get_method
        obj: BaseService = get(specification)
        self.update(obj, data)
        return obj


class Delete(Read):
    def erase(self, obj: BaseTable) -> None:
        try:
            self._session.delete(obj)
            self._session.commit()
        except Exception as e:
            self._session.rollback()
            raise e

    def delete(self, specification: Specification) -> dict[str, bool]:
        obj = self.get(specification)
        self.erase(obj)
        return {"ok": True}


class CreateRead(Create, Read):
    pass


class CreateReadUpdate(Update, CreateRead):
    pass


class CRUD(Delete, CreateReadUpdate):
    pass
