from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db_url = 'sqlite:///local.sqlite3'

engine = create_engine(db_url, echo=False, connect_args={'check_same_thread': False})

Session = sessionmaker(engine, autocommit=False, autoflush=False)


def get_session():
    session = Session()
    try:
        yield session
    finally:
        session.close()
