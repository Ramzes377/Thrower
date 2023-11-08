from api import crud_fabric, tables
from api.schemas import ID
from api.specification import SentMessageID

router = crud_fabric(
    table=tables.SentMessage,
    relative_path='sent_message',
    get_path='/{message_id}',
    response_model=ID,
    specification=SentMessageID
)
