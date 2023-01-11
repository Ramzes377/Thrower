from fastapi import Depends, APIRouter

from .services import SrvUser
from .specifications import UserID
from ..specifications import AppID, RoleID, UserID as MemberID
from ..dependencies import default_period
from ..schemas import Member, Session, IngameSeconds, DurationActivity

router = APIRouter(prefix='/user', tags=['user'])


@router.get('/', response_model=list[Member])
def all_users(service: SrvUser = Depends()):
    return service.all()


@router.post('/', response_model=Member)
def user(user_data: Member, service: SrvUser = Depends()):
    return service.post(user_data)


@router.get('/{user_id}', response_model=Member)
def user(user_id: UserID = Depends(), service: SrvUser = Depends()):
    return service.get(user_id)


@router.patch('/{user_id}', response_model=Member)
def user(userdata: Member | dict, user_id: UserID = Depends(), service: SrvUser = Depends()):
    return service.patch(user_id, userdata)


@router.get('/{user_id}/sessions', response_model=list[Session])
def user_sessions(user_id: UserID = Depends(), period=Depends(default_period), service: SrvUser = Depends()):
    sessions = service.get_sessions(user_id, **period)
    return sessions


@router.get('/{user_id}/activities', response_model=list[DurationActivity])
def user_activities(user_id: MemberID = Depends(), service: SrvUser = Depends()):
    return service.user_activities(user_id)


@router.get('/{user_id}/activities/{app_id}', response_model=list[DurationActivity])
def user_concrete_activity(user_id: MemberID = Depends(),
                           app_id: AppID = Depends(),
                           service: SrvUser = Depends()):
    specification = user_id & app_id
    return service.concrete_user_activity(specification)


@router.get('/{user_id}/activities/duration/', response_model=list[IngameSeconds])
def user_activities_durations(user_id: MemberID = Depends(), service: SrvUser = Depends()):
    return service.durations(user_id)


@router.get('/{user_id}/activities/duration/{role_id}', response_model=IngameSeconds)
def user_concrete_activity_duration(user_id: MemberID = Depends(),
                                    role_id: RoleID = Depends(),
                                    service: SrvUser = Depends()):
    return service.concrete_duration(user_id, role_id)
