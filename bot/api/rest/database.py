from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from config import Config
except ModuleNotFoundError:
    from bot.config import Config

engine = create_engine(
    Config.DB_URI,
    echo=False,
    connect_args={'check_same_thread': False}
)

Session = sessionmaker(engine, autocommit=False, autoflush=False)


def get_session():
    session = Session()
    try:
        yield session
    finally:
        session.close()
