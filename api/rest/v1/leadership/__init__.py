from fastapi import Depends, APIRouter

from .services import SrvLeadership
from ..specifications import SessionID, MessageID
from ..schemas import Leadership

router = APIRouter(prefix='/leadership', tags=['leadership'])


@router.post('/', response_model=Leadership)
def leadership(leadership: Leadership | dict, service: SrvLeadership = Depends()):
    return service.post(leadership)


@router.get('/{session_id}', response_model=list[Leadership])
def leadership(session_id: SessionID = Depends(), service: SrvLeadership = Depends()):
    return service.get(session_id)


@router.get('/{session_id}/leader/', response_model=Leadership)
def current_leader(session_id: SessionID = Depends(), service: SrvLeadership = Depends()):
    return service.current(session_id)


@router.get('/by_msg/{message_id}', response_model=list[Leadership])
def leadership(message_id: MessageID = Depends(), service: SrvLeadership = Depends()):
    return service.get(message_id)
