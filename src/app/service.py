import logging
from contextlib import suppress
from typing import (Callable, Any, Coroutine, Annotated, Optional, Protocol,
                    Type, TYPE_CHECKING)
from functools import partial

from fastapi import Depends, HTTPException, APIRouter, status, Query

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.config import Config
from src.constants import constants
from src.utils import (NotFoundException, CrudType, format_dict, table_to_json,
                       CoroItem)
from src.app.deffered import DeferredTasksProcessor
from src.app.dependencies import db_sessions

if TYPE_CHECKING:
    from sqlalchemy import UnaryExpression, Sequence, Select, BinaryExpression
    from sqlalchemy.ext.asyncio import AsyncSession

    from pydantic import BaseModel

    from src.app.tables import Base as BaseTable
    from src.app.specification import Specification

log = logging.getLogger(name='thrower.routers')


class Service:
    table: Optional['BaseTable'] = None
    order_by: Optional['UnaryExpression'] = None

    @property
    def _name(self):
        return self.table.__name__

    deferrer = DeferredTasksProcessor(sleep_seconds=Config.defer_sleep_seconds)

    @staticmethod
    async def wait_coro(coro: Coroutine, *args, **kwargs) -> Any:
        return await coro

    async def replicate(self,
                        coro_fabric: Callable,
                        repeat_on_failure: bool = False,
                        is_ordered: bool = True) -> Any:
        """
        Replicate simple coroutine execution
        require:
            positional first argument `session`.
        """
        log.debug(constants.log_reflect_begin(coro_fabric=coro_fabric))

        resp = await coro_fabric(session=self._session)
        if resp is not None:
            log.debug(
                constants.log_reflect_main_response(
                    response=table_to_json(resp))
            )

        for other_session in self._other_sessions:
            log.debug(constants.log_reflect_execution(session=other_session))
            await self.coro_handler(
                coro_item=CoroItem(coro_fabric=coro_fabric,
                                   coro_kwargs=dict(session=other_session),
                                   meta_kw=dict(
                                       repeat_on_failure=repeat_on_failure)
                                   ),
                is_ordered=is_ordered,
            )

        return resp

    def __init__(
            self,
            sessions: tuple['AsyncSession', ...] = Depends(db_sessions),
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
                       specification: 'Specification',
                       session_: Optional['AsyncSession'] = None,
                       suppress_error: bool = False,
                       **additional_filters: Any) -> Service:
        ...


class Create(Service):

    async def _create(self,
                      session: 'AsyncSession',
                      data: Optional[dict] = None,
                      object_: Optional['BaseTable'] = None,
                      suppress_unique_error: bool = True,
                      suppress_any_error: bool = False) \
            -> Optional['BaseModel']:
        if object_ is None:
            object_: 'BaseTable' = self.table(**data)

        async with session.begin() as transaction:
            try:
                o = constants.db_request(table_name=type(object_).__name__,
                                         specs=format_dict(data))
                log.debug(constants.log_object_creation(object=o))
                session.add(object_)
                with suppress(RuntimeError):
                    await session.flush()
            except IntegrityError as e:
                await transaction.rollback()
                log.debug(constants.log_unique_error)
                if not suppress_unique_error:
                    raise e
            except Exception as e:
                await transaction.rollback()
                log.exception(constants.log_creation_error(error=str(e)))
                if not suppress_any_error:
                    raise e
            else:
                await transaction.commit()

        return object_

    async def post(self,
                   data: 'BaseModel',
                   repeat_on_failure: bool = True) -> 'BaseTable':
        create = partial(self._create, data=data.model_dump())
        return await self.replicate(create, repeat_on_failure)


class Read(Service):

    @property
    def _query(self) -> 'Select':
        query = self._base_query
        if self._order_by is not None:
            query = query.order_by(self._order_by)
        return query

    def query(self, specification: 'Specification', *_, **kw) -> 'Select':
        return self._query.filter_by(**specification()).filter_by(**kw)

    async def get(self,
                  specification: Optional['Specification'] = None,
                  session_: 'AsyncSession' = None,
                  suppress_error: bool = False,
                  *,
                  _query: Optional['Select'] = None,
                  _ordering: 'UnaryExpression' = None,
                  **additional_filters: Any) -> 'BaseTable':

        session = session_ or self._session

        if (query := _query) is None:
            query = self.query(specification, **additional_filters)

        if _ordering is not None:
            query = query.order_by(_ordering)

        specs = specification() if specification else {}
        specs = format_dict({**specs, **additional_filters})
        db_request = constants.db_request(table_name=self._name, specs=specs)
        log.debug(constants.log_get_object(filters=db_request))

        async with session.begin():
            r = await session.execute(query)
            object_ = r.scalars().first()

        if object_ is None:

            details = constants.log_unavailable_object(details=db_request)
            log.debug(details)
            if not suppress_error:
                raise HTTPException(status_code=404, detail=details)

        params = table_to_json(object_) if object_ else {}
        db_request = constants.db_request(table_name=self._name,
                                          specs=format_dict(params))
        log.debug(constants.log_success_get(object=db_request))

        return object_

    async def all(self,
                  filter_: Optional['BinaryExpression'] = None,
                  specification: Optional['Specification'] = None,
                  *,
                  query: Optional['Select'] = None,
                  **kwargs) -> 'Sequence':
        specs = specification() if specification else {}
        specs = format_dict(specs)
        db_request = constants.db_request(table_name=self._name, specs=specs)
        log.debug(constants.log_all_rows(request=db_request,
                                         filter=filter_))

        query = self._query if query is None else query
        if filter_ is not None:
            query = query.filter(filter_)
        if specification is not None:
            query = query.filter_by(**specification())

        async with self._session.begin():
            r = (await self._session.execute(query)).scalars()

        r = r.all()

        log.debug(constants.log_success_all_get(count=len(r), type=self._name))

        return r


class Update(Read):
    @staticmethod
    async def update(object_: Service,
                     data: 'BaseModel',
                     session: 'AsyncSession') -> None:
        """ Update orm object  """

        log.debug(
            constants.log_update_object(type=type(object_).__name__,
                                        params=data)
        )

        for field in data.model_fields_set:
            field_value = getattr(data, field)
            setattr(object_, field, field_value)

        async with session.begin_nested():
            try:
                await session.commit()
                log.debug(constants.log_success_updated)
            except Exception as e:
                log.exception(constants.log_error_on_update(error=str(e)))
                await session.rollback()
                raise e

    async def patch(self,
                    specification: 'Specification',
                    data: 'BaseModel',
                    session_: Optional['AsyncSession'] = None,
                    *,
                    get_method: Optional[GetORM] = None,
                    suppress_error: bool = False,
                    **kwargs) -> 'BaseTable':

        async def _patch(_get: GetORM, session: 'AsyncSession') -> 'BaseTable':
            object_ = await _get(specification, session, suppress_error)

            if suppress_error and object_ is None:
                return None

            await self.update(object_, data, session)
            return object_

        get = get_method or self.get
        patch = partial(_patch, _get=get)

        return await self.replicate(patch)


class Delete(Read):
    @staticmethod
    async def erase(object_: 'BaseTable', session: 'AsyncSession') -> None:

        async with session.begin():
            try:
                await session.delete(object_)
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e

    async def delete(self, specification: 'Specification') -> None:

        specs = format_dict(specification())
        db_request = constants.db_request(table_name=self._name, specs=specs)

        async def _delete(session: 'AsyncSession'):
            log.debug(constants.log_delete_object(filters=db_request))

            if object_ := await self.get(specification, session_=session):
                return await self.erase(object_, session)

            log.debug(constants.log_cant_delete)

            raise NotFoundException

        await self.replicate(_delete)


class CreateRead(Create, Read):
    ...


class CreateReadUpdate(Update, CreateRead):
    ...


class CRUD(Delete, CreateReadUpdate):
    ...


def crud_fabric(table: 'BaseTable',
                relative_path: str,
                get_path: str,
                specification: 'Specification',
                response_model: Type['BaseModel'],
                *,
                include_in_schema: bool = True,
                with_all: bool = True,
                crud_type: CrudType = CrudType.CRUD) -> (APIRouter, Type[CRUD]):
    """ Build simple crud router. """

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
        return router, service_

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
        return router, service_

    @router.delete(get_path, include_in_schema=include_in_schema)
    async def delete_object(
            id_: specification = Depends(),
            service: service_ = Depends()
    ):
        return await service.delete(id_)

    return router, service_
