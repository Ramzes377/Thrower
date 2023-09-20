from fastapi import Depends, APIRouter, status

from .services import SrvUser
from api.schemas import User, Session, IngameSeconds, DurationActivity
from api.specification import AppID, RoleID, SessionMember, UserID

router = APIRouter(prefix='/user', tags=['user'])


@router.get('', response_model=list[User])
async def all_users(service: SrvUser = Depends()):
    return await service.all()


@router.post('', response_model=User, status_code=status.HTTP_201_CREATED)
async def user(user_data: User, service: SrvUser = Depends()):
    return await service.post(user_data)


@router.get('/{user_id}', response_model=User)
async def user(user_id: SessionMember = Depends(), service: SrvUser = Depends()):
    return await service.get(user_id)


@router.patch('/{user_id}', response_model=User)
async def user(
    userdata: dict,
    user_id: SessionMember = Depends(),
    service: SrvUser = Depends()
):
    return await service.patch(user_id, userdata)


@router.get('/{user_id}/sessions', response_model=list[Session])
async def user_sessions(
    user_id: SessionMember = Depends(),
    timestamps: SrvUser.filter_by_timeperiod = Depends(),
    service: SrvUser = Depends()
):
    sessions = await service.get_sessions(user_id, timestamps)
    return sessions


@router.get('/{user_id}/activities', response_model=list[DurationActivity])
async def user_activities(
    user_id: UserID = Depends(),
    service: SrvUser = Depends()
):
    return await service.user_activities(user_id)


@router.get('/{user_id}/activities/{app_id}',
            response_model=list[DurationActivity])
async def user_concrete_activity(
    user_id: UserID = Depends(),
    app_id: AppID = Depends(),
    service: SrvUser = Depends()
):
    specification = user_id & app_id
    return await service.user_activities(specification)


@router.get('/{user_id}/activities/duration/',
            response_model=list[IngameSeconds])
async def user_activities_durations(
    user_id: UserID = Depends(),
    service: SrvUser = Depends()
):
    a = await service.durations(user_id)
    return a


@router.get(
    '/{user_id}/activities/duration/{role_id}',
    response_model=IngameSeconds | None
)
async def user_concrete_activity_duration(
    user_id: UserID = Depends(),
    role_id: RoleID = Depends(),
    service: SrvUser = Depends()
):
    return await service.concrete_duration(user_id, role_id)
