from fastapi import Depends, APIRouter, status

from .services import SrvLeadership
from ..schemas import Leadership, LeaderChange
from ..specifications import SessionID

router = APIRouter(prefix='/leadership', tags=['leadership'])


@router.post('/', response_model=Leadership, status_code=status.HTTP_201_CREATED)
def leadership(leadership: Leadership | LeaderChange, service: SrvLeadership = Depends()):
    return service.post(leadership)


@router.get('/{session_id}/', response_model=Leadership)
def session_leader(session_id: SessionID = Depends(), service: SrvLeadership = Depends()):
    return service.get(session_id)


@router.get('/hist/{session_id}', response_model=list[Leadership])
def leadership(session_id: SessionID = Depends(), service: SrvLeadership = Depends()):
    return service.history(session_id)
