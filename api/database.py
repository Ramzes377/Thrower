import logging

from api.tables import SessionFabric
from config import Config

logger = logging.FileHandler('sqlalchemy.log')
logger.setLevel(logging.DEBUG)
logging.getLogger('sqlalchemy').addHandler(logger)

# Creating sessions in semi-manual mode

get_session_local = SessionFabric.build(
    db_uri=Config.local_db_uri,
    connect_args={"check_same_thread": False, "timeout": 120}
)

get_session_remote = SessionFabric.build(
    db_uri=Config.remote_db_uri,
)
