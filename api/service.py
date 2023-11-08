from functools import partial
from typing import Callable, Any, Coroutine, Annotated, Optional, Protocol

from pydantic import BaseModel
from fastapi import Depends, HTTPException, APIRouter, Query, status
from sqlalchemy import select, Select, Sequence
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import BinaryExpression

from config import Config
from utils import NotFoundException, CrudType
from constants import constants
from .deffered import DeferredTasksProcessor
from .specification import Specification
from .tables import Base as BaseTable
from .dependencies import db_sessions


class Service:
    table = None
    order_by = None

    deferrer = DeferredTasksProcessor(sleep_seconds=Config.defer_sleep_seconds)

    @staticmethod
    async def wait_coro(coro: Coroutine, *args, **kwargs) -> Any:
        return await coro

    async def reflect_execute(
            self,
            coro_fabric: Callable,
            is_ordered: bool = True
    ) -> Any:
        """
        Repeats simple coroutine execution if coro have
        positional first argument session.
        """

        resp = await coro_fabric(session=self._session)

        for other_session in self._other_sessions:
            await self.coro_handler(
                coro_fabric(session=other_session),
                is_ordered=is_ordered
            )

        return resp

    def __init__(
            self,
            sessions: tuple[AsyncSession, ...] = Depends(db_sessions),
            defer_handle: Annotated[
                bool, Query(include_in_schema=False)
            ] = True,
    ) -> None:
        self._session, *self._other_sessions = sessions
        self.defer_handle = defer_handle

        self.coro_handler = self.deferrer.add if defer_handle \
            else self.wait_coro

        self._base_query = select(self.table)
        self._order_by = Service.order_by


class GetORM(Protocol):
    async def __call__(self,
                       specification: Specification,
                       session_: AsyncSession = None,
                       suppress_error: bool = False,
                       **additional_filters: Any) -> Service:
        ...


class Create(Service):

    async def _create(self,
                      session: AsyncSession,
                      data: Optional[dict] = None,
                      object_: Optional[BaseTable] = None,
                      suppress_unique_error: bool = True,
                      suppress_any_error: bool = False) -> BaseModel | None:
        if object_ is None:
            object_: BaseTable = self.table(**data)

        async with session.begin_nested():
            try:
                session.add(object_)
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                if not suppress_unique_error:
                    raise e
            except Exception as e:
                await session.rollback()
                if not suppress_any_error:
                    raise e

        return object_

    async def post(self, data: BaseModel) -> BaseTable:
        create = partial(self._create, data=data.model_dump())
        return await self.reflect_execute(create)


class Read(Service):
    def _not_exists(self, specification: Specification):
        specs = ', '.join(f'{k} = {v}' for k, v in specification().items())
        details = constants.item_not_found(table_name=self.table.__name__,
                                           specs=specs)
        raise HTTPException(status_code=404, detail=details)

    @property
    def _query(self) -> Select:
        query = self._base_query
        if self._order_by is not None:
            query = query.order_by(self._order_by)
        return query

    def query(self, specification: Specification, *_, **kw) -> Select:
        return self._query.filter_by(**specification()).filter_by(**kw)

    async def get(self,
                  specification: Optional[Specification] = None,
                  session_: AsyncSession = None,
                  suppress_error: bool = False,
                  *,
                  _query: Optional[Select] = None,
                  _multiple_result: bool = False,
                  **additional_filters: Any) -> BaseTable:

        session = session_ or self._session

        if (query := _query) is None:
            query = self.query(specification, **additional_filters)

        async with session.begin():
            r = await session.execute(query)
            object_ = r.scalars().first()

        if object_ is None and not suppress_error:
            self._not_exists(specification)

        return object_

    async def all(self,
                  filter_: Optional[BinaryExpression] = None,
                  specification: Optional[Specification] = None,
                  *,
                  query: Select | None = None,
                  **kwargs) -> Sequence:
        query = self._query if query is None else query
        if filter_ is not None:
            query = query.filter(filter_)
        if specification is not None:
            query = query.filter_by(**specification())

        async with self._session.begin():
            r = (await self._session.execute(query)).scalars()
        return r.all()


class Update(Read):
    @staticmethod
    async def update(object_: Service,
                     data: BaseModel | dict,
                     session: AsyncSession) -> None:
        """ Update orm object  """

        iterable = data.items() if isinstance(data, dict) else data
        for k, v in iterable:
            setattr(object_, k, v)

        async with session.begin_nested():
            try:
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e

    async def patch(self,
                    specification: Specification,
                    data: BaseModel | dict,
                    session_: Optional[AsyncSession] = None,
                    *,
                    get_method: Optional[GetORM] = None,
                    suppress_error: bool = False,
                    _multiple_result: bool = False,
                    **kwargs) -> BaseTable:

        async def _patch(_get: GetORM, session: AsyncSession) -> BaseTable:
            object_ = await _get(specification, session, suppress_error,
                                 _multiple_result=_multiple_result)

            if suppress_error and object_ is None:
                return None

            await self.update(object_, data, session)
            return object_

        get = get_method or self.get
        patch = partial(_patch, _get=get)

        return await self.reflect_execute(patch)


class Delete(Read):
    @staticmethod
    async def erase(object_: BaseTable, session: AsyncSession) -> None:
        async with session.begin():
            try:
                await session.delete(object_)
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e

    async def delete(self, specification: Specification) -> None:
        async def _delete(session: AsyncSession):
            if object_ := await self.get(specification, session_=session):
                return await self.erase(object_, session)

            raise NotFoundException

        await self.reflect_execute(_delete)


class CreateRead(Create, Read):
    ...


class CreateReadUpdate(Update, CreateRead):
    ...


class CRUD(Delete, CreateReadUpdate):
    ...


def crud_fabric(table,
                relative_path: str,
                get_path: str,
                response_model: Any = dict,
                specification: Any = None,
                include_in_schema: bool = True,
                with_all: bool = True,
                crud_type: CrudType = CrudType.CRUD):
    router = APIRouter(prefix=f'/{relative_path}', tags=[relative_path])
    service_ = type(relative_path.capitalize(), (CRUD,), {'table': table})

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
        get_path,
        response_model=response_model,
        include_in_schema=include_in_schema,
    )
    async def get_object(
            id_: specification = Depends(),
            service: service_ = Depends()
    ):
        return await service.get(id_)

    if with_all:
        @router.get(
            '',
            response_model=list[response_model],
            include_in_schema=include_in_schema
        )
        async def all_rows(service: service_ = Depends()):
            return await service.all()

    if crud_type == CrudType.CR:
        return router

    @router.patch(
        get_path,
        response_model=response_model,
        include_in_schema=include_in_schema
    )
    async def patch_object(
            data: dict,
            id_: specification = Depends(),
            service: service_ = Depends()
    ):
        return await service.patch(id_, data)

    if crud_type == CrudType.CRU:
        return router

    @router.delete(get_path, include_in_schema=include_in_schema)
    async def delete_object(
            id_: specification = Depends(),
            service: service_ = Depends()
    ):
        return await service.delete(id_)

    return router
