from datetime import datetime

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_session_local, get_session_remote
from utils import now


def default_period(begin: datetime | None = None, end: datetime | None = None):
    return {
        'begin': begin or datetime.utcfromtimestamp(0),
        'end': end or now()
    }


def limit(amount: int = 20) -> int:
    return amount


def params_guild_id(guild_id: int = 0) -> int:
    return guild_id


def db_sessions(
        main_session: AsyncSession = Depends(get_session_local),
        remote_session: AsyncSession = Depends(get_session_remote),
) -> tuple[AsyncSession]:
    yield main_session, remote_session
