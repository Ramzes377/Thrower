from typing import Callable, Any

from pydantic import BaseModel
from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query
from sqlalchemy.sql.elements import BinaryExpression
from starlette import status

from config import Config
from . import tables
from .specification import Specification, ID
from .tables import Base as BaseTable
from api.database import get_session, async_session


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


def create_simple_crud(
    table,
    endpoint_prefix: str,
    path: str,
    response_model: Any = dict,
    include_in_schema: bool = True,
):
    sub = '{' + path + '}'
    filter_path = f'/{sub}'

    router = APIRouter(prefix=f'/{endpoint_prefix}', tags=[endpoint_prefix])

    Service = type(endpoint_prefix, (CRUD,), {'table': table})

    @router.get(
        '',
        response_model=list[response_model],
        include_in_schema=include_in_schema
    )
    async def all_rows(service: Service = Depends()):
        return await service.all()

    @router.post(
        '',
        status_code=status.HTTP_201_CREATED,
        response_model=response_model,
        include_in_schema=include_in_schema,
    )
    async def post_object(
        message: response_model,
        service: Service = Depends()
    ):
        return await service.post(message)

    @router.get(
        filter_path,
        response_model=response_model,
        include_in_schema=include_in_schema,
    )
    async def get_object(
        id: ID = Depends(),
        service: Service = Depends()
    ):
        return await service.get(id)

    @router.patch(
        filter_path,
        response_model=response_model,
        include_in_schema=include_in_schema
    )
    async def patch_object(
        data: dict,
        id: ID = Depends(),
        service: Service = Depends()
    ):
        return await service.patch(id, data)

    @router.delete(filter_path, include_in_schema=include_in_schema)
    async def delete_object(
        id: ID = Depends(),
        service: Service = Depends()
    ):
        return await service.delete(id)

    return router


async def init_configs():
    guild_id = Config.GUILD_ID

    async with async_session() as session:
        stmt = await session.scalars(
            select(tables.Guild).filter_by(id=guild_id)
        )
        guild = stmt.first()

    Config.CREATE_CHANNEL_ID = guild.create.id

    Config.LOGGER_ID = guild.logger.id
    Config.ROLE_REQUEST_ID = guild.role_request.id
    Config.COMMAND_ID = guild.command.id

    Config.IDLE_CATEGORY_ID = guild.idle_category.id
    Config.PLAYING_CATEGORY_ID = guild.playing_category.id

