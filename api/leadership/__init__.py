from fastapi import Depends, APIRouter, status

from .services import SrvLeadership
from api.schemas import Leadership, LeaderChange
from api.specification import SessionID

router = APIRouter(prefix='/leadership', tags=['leadership'])


@router.post('', response_model=Leadership, status_code=status.HTTP_201_CREATED)
async def leadership(
    leadership: Leadership | LeaderChange,
    service: SrvLeadership = Depends()
):
    return await service.post(leadership)


@router.get('/{session_id}', response_model=Leadership)
async def session_leader(
    session_id: SessionID = Depends(),
    service: SrvLeadership = Depends()
):
    return await service.get(session_id)


@router.get('/hist/{session_id}', response_model=list[Leadership])
async def leadership(
    session_id: SessionID = Depends(),
    service: SrvLeadership = Depends()
):
    return await service.history(session_id)