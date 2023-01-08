from fastapi import Depends, APIRouter

from ..schemas import Leadership
from .services import SrvLeadership

router = APIRouter(prefix='/leadership', tags=['leadership'])


@router.get('/{session_id}', response_model=list[Leadership])
def leadership(session_id: int, service: SrvLeadership = Depends()):
    return service.get(session_id)


@router.post('/', response_model=Leadership)
def leadership(leadershipdata: Leadership | dict, service: SrvLeadership = Depends()):
    return service.post(leadershipdata)


@router.get('/{session_id}/leader/', response_model=Leadership)
def current_leader(session_id: int, service: SrvLeadership = Depends()):
    return service.current(session_id)


@router.get('/by_msg/{message_id}', response_model=list[Leadership])
def leadership(message_id: int, service: SrvLeadership = Depends()):
    return service.get(message_id=message_id)
