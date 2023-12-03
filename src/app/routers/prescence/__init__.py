from fastapi import Depends, APIRouter, status

from .services import SrvPrescence
from src.app.schemas import SessionLike
from src.app.specification import SessionID, MessageID

router = APIRouter(prefix='/prescence', tags=['prescence'])


@router.post('', response_model=SessionLike, status_code=status.HTTP_201_CREATED)
async def prescence_create(
        prescencedata: SessionLike,
        service: SrvPrescence = Depends()
):
    return await service.post(prescencedata)


@router.patch('', response_model=SessionLike)
async def prescence_update(
        prescencedata: SessionLike,
        service: SrvPrescence = Depends()
):
    return await service.patch(prescencedata)


@router.get('/{session_id}', response_model=list[SessionLike])
async def prescence_get(
        session_id: SessionID = Depends(),
        service: SrvPrescence = Depends()
):
    return await service.all(specification=session_id)


@router.get('/by_msg/{message_id}', response_model=list[SessionLike])
async def prescence_get_by_msg_id(
        message_id: MessageID = Depends(),
        service: SrvPrescence = Depends()
):
    return await service.all(specification=message_id, join_sessions=True)
