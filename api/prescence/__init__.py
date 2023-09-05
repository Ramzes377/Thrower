from fastapi import Depends, APIRouter, status

from .services import SrvPrescence
from api.schemas import Prescence, EndPrescence
from api.specification import SessionID, MessageID

router = APIRouter(prefix='/prescence', tags=['prescence'])


@router.post('', response_model=Prescence, status_code=status.HTTP_201_CREATED)
async def prescence(prescencedata: Prescence, service: SrvPrescence = Depends()):
    return await service.post(prescencedata)


@router.patch('', response_model=Prescence)
async def prescence(prescencedata: EndPrescence, service: SrvPrescence = Depends()):
    return await service.patch(prescencedata)


@router.get('/{session_id}', response_model=list[Prescence])
async def prescence(session_id: SessionID = Depends(), service: SrvPrescence = Depends()):
    return await service.get(session_id)


@router.get('/by_msg/{message_id}', response_model=list[Prescence])
async def prescence(message_id: MessageID = Depends(), service: SrvPrescence = Depends()):
    return await service.get(message_id)
