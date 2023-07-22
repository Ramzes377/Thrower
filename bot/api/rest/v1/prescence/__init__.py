from fastapi import Depends, APIRouter, status

from .services import SrvPrescence
from ..schemas import Prescence, EndPrescence
from ..specifications import SessionID, MessageID

router = APIRouter(prefix='/prescence', tags=['prescence'])


@router.post('/', response_model=Prescence, status_code=status.HTTP_201_CREATED)
def prescence(prescencedata: Prescence, service: SrvPrescence = Depends()):
    return service.post(prescencedata)


@router.patch('/', response_model=Prescence)
def prescence(prescencedata: EndPrescence, service: SrvPrescence = Depends()):
    return service.patch(prescencedata)


@router.get('/{session_id}', response_model=list[Prescence])
def prescence(session_id: SessionID = Depends(), service: SrvPrescence = Depends()):
    return service.get(session_id)


@router.get('/by_msg/{message_id}', response_model=list[Prescence])
def prescence(message_id: MessageID = Depends(), service: SrvPrescence = Depends()):
    return service.get(message_id)
