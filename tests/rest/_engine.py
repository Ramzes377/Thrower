from sqlmodel.pool import StaticPool
from sqlmodel import create_engine
from api.rest.v1.tables import Base

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
Base.metadata.create_all(engine)
