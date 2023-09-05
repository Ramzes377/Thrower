from typing import Callable, Any

from pydantic import BaseModel
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query
from sqlalchemy.sql.elements import BinaryExpression

from .specification import Specification
from .tables import Base as BaseTable
from api.database import get_session


class Service:
    table = None
    order_by = None

    def __init__(self, session: AsyncSession = Depends(get_session)):
        self._session = session
        self._base_query = select(self.table)
        self._order_by = Service.order_by


class Create(Service):
    async def create(self, obj: BaseModel) -> None:
        try:
            self._session.add(obj)
            await self._session.commit()
            return obj
        except Exception as e:
            await self._session.rollback()
            raise e

    async def post(self, data: BaseModel) -> BaseTable:
        orm = self.table(**data.model_dump())
        return await self.create(orm)


class Read(Service):
    def _is_exist(self, obj: BaseTable, specification: Specification):
        if not obj:
            specs = ', '.join(
                f'[{k} = {v}]' for k, v in specification().items()
            )
            details = f"Row of table {self.table.__name__} " \
                      f"with follows params ({specs}) not found"
            raise HTTPException(status_code=404, detail=details)

    @property
    def _query(self) -> Query:
        query = self._base_query
        if self._order_by is not None:
            query = query.order_by(self._order_by)
        return query

    def _get(self, specification: Specification) -> Query:
        return self._query.filter_by(**specification())

    async def get(
        self,
        specification: Specification,
        *args: Any,
        **kwargs: Any
    ) -> BaseTable:

        r = await self._session.scalars(self._get(specification))
        obj = r.first()
        self._is_exist(obj, specification)
        return obj

    async def all(
        self,
        filter_: BinaryExpression = None,
        *,
        query: Query | None = None,
        **kwargs
    ) -> list[BaseTable]:

        query = self._query if query is None else query
        if filter_ is not None:
            query = query.filter(filter_)

        r = await self._session.scalars(query)
        return r.all()


class Update(Read):
    async def update(self, obj: Service, data: BaseModel | dict) -> None:
        try:
            iterable = data.items() if isinstance(data, dict) else data
            for k, v in iterable:
                setattr(obj, k, v)
            await self._session.commit()
        except Exception as e:
            await self._session.rollback()
            raise e

    async def patch(
        self,
        specification: Specification,
        data: BaseModel | dict,
        *args,
        get_method: Callable = None,
        **kwargs
    ) -> BaseTable:
        get = get_method or self.get
        obj: Service = await get(specification)
        self._is_exist(obj, specification)
        await self.update(obj, data)
        return obj


class Delete(Read):
    async def erase(self, obj: BaseTable) -> None:
        try:
            await self._session.delete(obj)
            await self._session.commit()
        except Exception as e:
            await self._session.rollback()
            raise e

    async def delete(self, specification: Specification) -> None:
        obj = await self.get(specification)
        await self.erase(obj)


class CreateRead(Create, Read):
    pass


class CreateReadUpdate(Update, CreateRead):
    pass


class CRUD(Delete, CreateReadUpdate):
    pass
