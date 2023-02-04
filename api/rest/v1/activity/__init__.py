from fastapi import Depends, APIRouter, status

from .services import SrvActivities
from ..schemas import Activity, Role, ActivityInfo, Emoji, EndActivity
from ..specifications import AppID

router = APIRouter(prefix='/activity', tags=['activity'])


@router.post('/', response_model=Activity, status_code=status.HTTP_201_CREATED)
def activity(activitydata: Activity, service: SrvActivities = Depends()):
    return service.post(activitydata)


@router.patch('/', response_model=Activity)
def activity(activitydata: EndActivity, service: SrvActivities = Depends()):
    return service.patch(activitydata)


@router.get('/', response_model=list[Activity])
def all_activities(timestamps: SrvActivities.filter_by_timeperiod = Depends(), service: SrvActivities = Depends()):
    return service.all(timestamps)


@router.get('/{app_id}', response_model=Activity)
def activity(app_id: AppID = Depends(), service: SrvActivities = Depends()):
    return service.get(app_id)


@router.get('/{app_id}/info', response_model=ActivityInfo)
def activity_info(app_id: AppID = Depends(), service: SrvActivities = Depends()):
    activity = service.get(app_id)
    return activity.info


@router.get('/{app_id}/role', response_model=Role)
def activity_role(app_id: AppID = Depends(), service: SrvActivities = Depends()):
    activity = service.get(app_id)
    info = activity.info
    return info.role


@router.get('/{app_id}/emoji', response_model=Emoji)
def activity_emoji(app_id: AppID = Depends(), service: SrvActivities = Depends()):
    activity = service.get(app_id)
    info = activity.info
    role = info.role
    return role.emoji
