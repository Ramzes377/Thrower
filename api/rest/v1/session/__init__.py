from fastapi import Depends, APIRouter

from ..schemas import Session, Member, Prescence, Activity, Leadership
from .services import SrvSession

router = APIRouter(prefix='/session', tags=['session'])


@router.get('/{session_id}', response_model=Session)
def session(session_id: int, service: SrvSession = Depends()):
    return service.get(session_id)


@router.put('/{session_id}', response_model=Session)
def session(session_id: int, sessdata: Session, service: SrvSession = Depends()):
    return service.put(session_id, sessdata)


@router.post('/', response_model=Session)
def session(sessdata: Session, service: SrvSession = Depends()):
    return service.post(sessdata)


@router.get('/{session_id}/members', response_model=list[Member])
def session_users(session_id: int, service: SrvSession = Depends()):
    return service.get_members(session_id)


@router.post('/{session_id}/members/{user_id}', response_model=Member)
def session_users(session_id: int, user_id: int, service: SrvSession = Depends()):
    return service.add_member(session_id, user_id)


@router.get('/{session_id}/prescence', response_model=list[Prescence])
def session_prescence(session_id: int, service: SrvSession = Depends()):
    return service.get_prescence(session_id)


@router.get('/{session_id}/activities', response_model=list[Activity])
def session_activities(session_id: int, service: SrvSession = Depends()):
    return service.get_activities(session_id)


@router.get('/{message_id}/leadership', response_model=list[Leadership])
def session_leadership(message_id: int, service: SrvSession = Depends()):
    return service.get_leadership(message_id)


@router.get('/by_msg/{message_id}', response_model=Session)
def session(message_id: int, service: SrvSession = Depends()):
    return service.get_by_msgid(message_id)


@router.get('/by_leader/{leader_id}', response_model=Session)
def session(leader_id: int, service: SrvSession = Depends()):
    return service.get_by_leader(leader_id)


@router.get('/unclosed/', response_model=list[Session])
def get_unclosed(service: SrvSession = Depends()):
    return service.get_unclosed()


@router.get('/all/', response_model=list[Session])
def sessions(service: SrvSession = Depends()):
    return service.get_all()


@router.get('/activities/by_msg/{msg_id}', response_model=list[Activity])
def session_activities(msg_id: int, service: SrvSession = Depends()):
    return service.get_activities_by_msg(msg_id)
