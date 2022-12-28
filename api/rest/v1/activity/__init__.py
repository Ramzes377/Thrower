from datetime import datetime

from fastapi import Depends, APIRouter

from api.bot.vars import tzMoscow
from .services import SrvActivities
from ..schemas import Activity, Role, ActivityInfo, Emoji, IngameSeconds

router = APIRouter(prefix='/activity', tags=['activity'])


@router.get('/{app_id}', response_model=Activity)
def activity(app_id: int, service: SrvActivities = Depends()):
    return service.get(app_id)


@router.get('/{app_id}/info', response_model=ActivityInfo)
def activity_info(app_id: int, service: SrvActivities = Depends()):
    return service.get_info(app_id)


@router.get('/{app_id}/role', response_model=Role)
def activity_role(app_id: int, service: SrvActivities = Depends()):
    return service.get_role(app_id)


@router.get('/{app_id}/emoji', response_model=Emoji)
def activity_role(app_id: int, service: SrvActivities = Depends()):
    return service.get_emoji(app_id)


@router.post('/', response_model=Activity)
def activity(activitydata: Activity, service: SrvActivities = Depends()):
    return service.post(activitydata)


@router.put('/', response_model=Activity)
def activity(activitydata: Activity | dict, service: SrvActivities = Depends()):
    return service.put(activitydata)


@router.get('/all/', response_model=list[Activity])
def activies(begin: datetime = datetime.fromordinal(1), end: datetime = None, service: SrvActivities = Depends()):
    end = datetime.now(tz=tzMoscow) if end is None else end
    return service.get_all(begin, end)


@router.get('/user/{user_id}', response_model=list[Activity])
def user_app_sessions(user_id: int, service: SrvActivities = Depends()):
    return service.user_app_sessions(user_id)


@router.get('/user/{user_id}/{app_id}', response_model=list[Activity])
def user_concrete_app_sessions(user_id: int, app_id: int, service: SrvActivities = Depends()):
    return service.user_concrete_app_sessions(user_id, app_id)


@router.get('/user/{user_id}/ingame/', response_model=list[IngameSeconds]) #
def user_all_game_time(user_id: int, service: SrvActivities = Depends()):
    return service.user_ingame_seconds(user_id)


@router.get('/user/{user_id}/ingame/{role_id}', response_model=IngameSeconds | None) #
def user_concrete_game_time(user_id: int, role_id: int, service: SrvActivities = Depends()):
    return service.user_concrete_game_seconds(user_id, role_id)
