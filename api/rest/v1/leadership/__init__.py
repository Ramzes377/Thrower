from fastapi import Depends, APIRouter

from .services import SrvLeadership
from ..specifications import SessionID, MessageID
from ..schemas import Leadership, LeaderChange

router = APIRouter(prefix='/leadership', tags=['leadership'])


@router.post('/', response_model=Leadership)
def leadership(leadership: Leadership | LeaderChange, service: SrvLeadership = Depends()):
    return service.post(leadership)


@router.get('/{session_id}/', response_model=Leadership)
def session_leader(session_id: SessionID = Depends(), service: SrvLeadership = Depends()):
    return service.get(session_id)


@router.get('/hist/{session_id}', response_model=list[Leadership])
def leadership(session_id: SessionID = Depends(), service: SrvLeadership = Depends()):
    return service.history(session_id)


@router.get('/hist/by_msg/{message_id}', response_model=list[Leadership])
def leadership(message_id: MessageID = Depends(), service: SrvLeadership = Depends()):
    return service.history(message_id)
