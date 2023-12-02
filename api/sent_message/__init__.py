from api import tables
from api import crud_fabric
from api.schemas import SentMessage
from api.specification import SentMessageID

router = crud_fabric(
    table=tables.SentMessage,
    relative_path='sent_message',
    get_path='/{message_id}',
    response_model=SentMessage,
    specification=SentMessageID
)
