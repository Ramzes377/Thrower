from fastapi import Depends, APIRouter

from .services import SrvActivities
from ..dependencies import default_period
from ..schemas import Activity, Role, ActivityInfo, Emoji
from ..specifications import AppID

router = APIRouter(prefix='/activity', tags=['activity'])


@router.post('/', response_model=Activity)
def activity(activitydata: Activity, service: SrvActivities = Depends()):
    return service.post(activitydata)


@router.patch('/', response_model=Activity)
def activity(activitydata: Activity | dict, service: SrvActivities = Depends()):
    return service.patch(activitydata)


@router.get('/', response_model=list[Activity])
def all_activities(period=Depends(default_period), service: SrvActivities = Depends()):
    return service.all(**period)


@router.get('/{app_id}', response_model=Activity)
def activity(app_id: AppID = Depends(), service: SrvActivities = Depends()):
    return service.get(app_id)


@router.get('/{app_id}/info', response_model=ActivityInfo)
def activity_info(app_id: AppID = Depends(), service: SrvActivities = Depends()):
    return service.get(app_id).info


@router.get('/{app_id}/role', response_model=Role)
def activity_role(app_id: AppID = Depends(), service: SrvActivities = Depends()):
    return service.get(app_id).info.role


@router.get('/{app_id}/emoji', response_model=Emoji)
def activity_emoji(app_id: AppID = Depends(), service: SrvActivities = Depends()):
    return service.get(app_id).info.role.emoji
