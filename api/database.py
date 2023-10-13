import logging

from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine,
    async_sessionmaker,
)

from api.tables import session_fabric
from config import Config

logger = logging.FileHandler('sqlalchemy.log')
logger.setLevel(logging.DEBUG)
logging.getLogger('sqlalchemy').addHandler(logger)

engine = create_async_engine(
    Config.DB_URI,
    echo=False,
    connect_args={"check_same_thread": False, "timeout": 120}
)
async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

get_session = session_fabric(async_session, engine)
