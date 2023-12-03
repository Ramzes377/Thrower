from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.app import tables
from src.app.service import CRUD
from src.app.tables import Base as BaseTable


class SrvRole(CRUD):
    table = tables.Role

    def get(self,
            *args,
            guild_id: Optional[int] = None,
            session_: Optional[AsyncSession] = None) -> BaseTable:
        if guild_id is not None:
            return super().get(*args, guild_id=guild_id, session_=session_)
        return super().get(*args, session_=session_)
