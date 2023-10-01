from fastapi import Depends, APIRouter, status

from .services import SrvSentMessage
from api.schemas import ID
from api.specification import SentMessageID

router = APIRouter(prefix='/sent_message', tags=['sent_message'])


@router.get('', response_model=list[ID])
async def all_messages(service: SrvSentMessage = Depends()):
    return await service.all()


@router.post('', response_model=ID,
             status_code=status.HTTP_201_CREATED)
async def post_message(
    message: ID,
    service: SrvSentMessage = Depends()
):
    return await service.post(message)


@router.get('/{message_id}', response_model=ID)
async def get_message(
    message_id: SentMessageID = Depends(),
    service: SrvSentMessage = Depends()
):
    return await service.get(message_id)


@router.delete('/{message_id}')
async def delete_message(
    message_id: SentMessageID = Depends(),
    service: SrvSentMessage = Depends()
):
    return await service.delete(message_id)
