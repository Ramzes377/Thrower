from datetime import datetime

from fastapi import Depends, APIRouter

from settings import tzMoscow
from .services import SrvSession
from ..schemas import Session, Member, Prescence, Activity, Leadership

router = APIRouter(prefix='/session', tags=['session'])


@router.get('/{session_id}', response_model=Session)
def session(session_id: int, service: SrvSession = Depends()):
    return service.get(session_id)


@router.put('/{session_id}', response_model=Session)
def session(session_id: int, sessdata: Session | dict, service: SrvSession = Depends()):
    return service.put(session_id, sessdata)


@router.post('/', response_model=Session)
def session(session: Session, service: SrvSession = Depends()):
    return service.post(session)


@router.get('/all/', response_model=list[Session])
def sessions(begin: datetime = datetime.fromordinal(1), end: datetime = None, service: SrvSession = Depends()):
    end = datetime.now(tz=tzMoscow) if end is None else end
    return service.all(begin, end)


@router.get('/{session_id}/members', response_model=list[Member])
def session_users(session_id: int, service: SrvSession = Depends()):
    return service.members(session_id)


@router.post('/{session_id}/members/{user_id}', response_model=Member)
def session_users(session_id: int, user_id: int, service: SrvSession = Depends()):
    return service.add_member(session_id, user_id)


@router.get('/{session_id}/prescence', response_model=list[Prescence])
def session_prescence(session_id: int, service: SrvSession = Depends()):
    return service.prescence(session_id)


@router.get('/{session_id}/activities', response_model=list[Activity])
def session_activities(session_id: int, service: SrvSession = Depends()):
    return service.activities(session_id)


@router.get('/{message_id}/leadership', response_model=list[Leadership])
def session_leadership(message_id: int, service: SrvSession = Depends()):
    return service.leadership(message_id)


@router.get('/by_msg/{message_id}', response_model=Session)
def session(message_id: int, service: SrvSession = Depends()):
    return service.get(message_id=message_id)


@router.get('/by_msg/{message_id}/activities', response_model=list[Activity])
def session_activities(message_id: int, service: SrvSession = Depends()):
    return service.activities_by_msg(message_id)


@router.get('/unclosed/', response_model=list[Session])
def get_unclosed(service: SrvSession = Depends()):
    return service.unclosed()


@router.get('/unclosed/{leader_id}', response_model=Session)
def session(leader_id: int, service: SrvSession = Depends()):
    return service.get(leader_id=leader_id)
