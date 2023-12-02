from fastapi import Depends, APIRouter, status

from .services import SrvLeadership
from api.schemas import SessionLike
from api.specification import SessionID

router = APIRouter(prefix='/leadership', tags=['leadership'])


@router.post('', response_model=SessionLike, status_code=status.HTTP_201_CREATED)
async def leadership_create(
    leadership: SessionLike,
    service: SrvLeadership = Depends()
):
    return await service.post(leadership)


@router.get('/{session_id}', response_model=SessionLike)
async def session_leader(
    session_id: SessionID = Depends(),
    service: SrvLeadership = Depends()
):
    return await service.get(session_id)


@router.get('/hist/{session_id}', response_model=list[SessionLike])
async def leadership_get(
    session_id: SessionID = Depends(),
    service: SrvLeadership = Depends()
):
    return await service.history(session_id)
