from src.app import tables
from src.app.service import crud_fabric
from src.app.schemas import SentMessage
from src.app.specification import SentMessageID

router, _ = crud_fabric(
    table=tables.SentMessage,
    relative_path='sent_message',
    get_path='/{message_id}',
    response_model=SentMessage,
    specification=SentMessageID
)
