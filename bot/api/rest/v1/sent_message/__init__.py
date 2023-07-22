from fastapi import Depends, APIRouter, status

from .services import SrvSentMessage
from ..schemas import SentMessage
from ..specifications import ID

router = APIRouter(prefix='/sent_message', tags=['sent_message'])


@router.get('/', response_model=list[SentMessage])
def all_messages(service: SrvSentMessage = Depends()):
    return service.all()


@router.post('/', response_model=SentMessage, status_code=status.HTTP_201_CREATED)
def post_message(message: SentMessage, service: SrvSentMessage = Depends()):
    return service.post(message)


@router.get('/{id}', response_model=SentMessage)
def get_message(id: ID = Depends(), service: SrvSentMessage = Depends()):
    return service.get(id)


@router.delete('/{id}')
def delete_message(id: ID = Depends(), service: SrvSentMessage = Depends()):
    return service.delete(id)
