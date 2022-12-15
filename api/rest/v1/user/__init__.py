from datetime import datetime

from fastapi import Depends, APIRouter

from api.bot.vars import tzMoscow
from ..schemas import Member, Session, Activity
from .services import SrvUser

router = APIRouter(prefix='/user', tags=['user'])


@router.get('/{user_id}', response_model=Member)
def user(user_id: int, service: SrvUser = Depends()):
    return service.get(user_id)


@router.post('/', response_model=Member)
def user(userdata: Member, service: SrvUser = Depends()):
    return service.post(userdata)


@router.put('/{user_id}', response_model=Member)
def user(user_id: int, userdata: Member | dict, service: SrvUser = Depends()):
    return service.put(user_id, userdata)


@router.get('/all/', response_model=list[Member])
def users(service: SrvUser = Depends()):
    return service.get_all()


@router.get('/{user_id}/sessions', response_model=list[Session])
def user_sessions(user_id: int,
                  begin: datetime = datetime.fromordinal(1),
                  end: datetime = None,
                  service: SrvUser = Depends()):
    end = datetime.now(tz=tzMoscow) if end is None else end
    sessions = service.get_sessions(user_id, begin, end)
    return sessions


@router.get('/{user_id}/activities', response_model=list[Activity])
def user_activities(user_id: int, service: SrvUser = Depends()):
    return service.get_activities(user_id)
