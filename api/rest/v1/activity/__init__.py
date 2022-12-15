from datetime import datetime

from fastapi import Depends, APIRouter

from api.bot.vars import tzMoscow
from .services import SrvActivities
from ..schemas import Activity, Role, ActivityInfo, Emoji

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
