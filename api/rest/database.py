from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.bot.vars import database_URL

db_url = database_URL

engine = create_engine(db_url, echo=False, connect_args={'check_same_thread': False})

Session = sessionmaker(engine, autocommit=False, autoflush=False)


def get_session():
    session = Session()
    try:
        yield session
    finally:
        session.close()
