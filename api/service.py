from typing import Callable, Any, Union

from pydantic import BaseModel
from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import select, Select, Sequence
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import BinaryExpression
from starlette import status

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
    async def create(
            self,
            obj: BaseModel,
            suppress_unique_error: bool = True
    ) -> BaseModel | None:
        try:
            self._session.add(obj)
            await self._session.commit()
            return obj
        except IntegrityError as e:
            if not suppress_unique_error:
                raise e
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
    def _query(self) -> Select:
        query = self._base_query
        if self._order_by is not None:
            query = query.order_by(self._order_by)
        return query

    def _get(self, specification: Specification, *_, **kw) -> Select:
        return self._query.filter_by(**specification()).filter_by(**kw)

    async def get(
            self,
            specification: Specification,
            *args: Any,
            **kw: Any
    ) -> BaseTable:

        r = await self._session.scalars(self._get(specification, **kw))
        obj = r.first()
        self._is_exist(obj, specification)
        return obj

    async def all(
            self,
            filter_: BinaryExpression = None,
            *,
            query: Select | None = None,
            **kwargs    # noqa
    ) -> Sequence:

        query = self._query if query is None else query
        if filter_ is not None:
            query = query.filter(filter_)

        r = await self._session.scalars(query)
        return r.all()


class Update(Read):
    async def update(
            self,
            obj: Union[Service, Any],
            data: BaseModel | dict
    ) -> None:
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


def crud_fabric(
        table,
        prefix: str,
        path: str,
        response_model: Any = dict,
        specification: Any = None,
        include_in_schema: bool = True,
):
    router = APIRouter(prefix=f'/{prefix}', tags=[prefix])
    service_ = type(prefix.capitalize(), (CRUD,), {'table': table})

    @router.get(
        '',
        response_model=list[response_model],
        include_in_schema=include_in_schema
    )
    async def all_rows(service: service_ = Depends()):
        return await service.all()

    @router.post(
        '',
        status_code=status.HTTP_201_CREATED,
        response_model=response_model,
        include_in_schema=include_in_schema,
    )
    async def post_object(
            message: response_model,
            service: service_ = Depends()
    ):
        return await service.post(message)

    @router.get(
        path,
        response_model=response_model,
        include_in_schema=include_in_schema,
    )
    async def get_object(
            id: specification = Depends(),
            service: service_ = Depends()
    ):
        return await service.get(id)

    @router.patch(
        path,
        response_model=response_model,
        include_in_schema=include_in_schema
    )
    async def patch_object(
            data: dict,
            id: specification = Depends(),
            service: service_ = Depends()
    ):
        return await service.patch(id, data)

    @router.delete(path, include_in_schema=include_in_schema)
    async def delete_object(
            id: specification = Depends(),
            service: service_ = Depends()
    ):
        return await service.delete(id)

    return router
