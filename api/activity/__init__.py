from fastapi import Depends, APIRouter, status

from .services import SrvActivities
from api.schemas import Activity, Role, ActivityInfo, Emoji, EndActivity
from api.specification import AppID

router = APIRouter(prefix='/activity', tags=['activity'])


@router.post('', response_model=Activity, status_code=status.HTTP_201_CREATED)
async def activity(activitydata: Activity, service: SrvActivities = Depends()):
    return await service.post(activitydata)


@router.patch('', response_model=Activity)
async def activity(
    activitydata: EndActivity,
    service: SrvActivities = Depends()
):
    return await service.patch(activitydata)


@router.get('', response_model=list[Activity])
async def all_activities(
    timestamps: SrvActivities.filter_by_timeperiod = Depends(),
    service: SrvActivities = Depends()
):
    return await service.all(timestamps)


@router.get('/{app_id}', response_model=Activity)
async def activity(
    app_id: AppID = Depends(),
    service: SrvActivities = Depends()
):
    return await service.get(app_id)


@router.get('/{app_id}/info', response_model=ActivityInfo | None)
async def activity_info(
    app_id: AppID = Depends(),
    service: SrvActivities = Depends()
):
    activity = await service.get(app_id)
    return activity.info


@router.get('/{app_id}/role', response_model=Role)
async def activity_role(
    app_id: AppID = Depends(),
    service: SrvActivities = Depends()
):
    activity = await service.get(app_id)
    info = activity.info
    return info.role


@router.get('/{app_id}/emoji', response_model=Emoji)
async def activity_emoji(
    app_id: AppID = Depends(),
    service: SrvActivities = Depends()
):
    activity = await service.get(app_id)
    info = activity.info
    role = info.role
    return role.emoji
