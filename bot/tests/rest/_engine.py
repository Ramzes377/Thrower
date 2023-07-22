from os import environ, getcwd

from sqlmodel import create_engine
from sqlmodel.pool import StaticPool

environ['ENV_PATH'] = './bot/env/test.env'

print(getcwd())

from bot.api.rest.v1.tables import Base

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
Base.metadata.create_all(engine)
