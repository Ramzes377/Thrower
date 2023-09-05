from fastapi import Depends, APIRouter, status

from .services import SrvActivityInfo
from api.schemas import ActivityInfo
from api.specification import ActivityID

router = APIRouter(prefix='/activity_info', tags=['activity_info'])


@router.post('', response_model=ActivityInfo,
             status_code=status.HTTP_201_CREATED)
async def post(
    activity_info: ActivityInfo,
    service: SrvActivityInfo = Depends()
):
    return await service.post(activity_info)


@router.get('/{app_id}', response_model=ActivityInfo)
async def get(
    app_id: ActivityID = Depends(),
    service: SrvActivityInfo = Depends()
):
    return await service.get(app_id)


@router.get('', response_model=list[ActivityInfo])
async def get_all(service: SrvActivityInfo = Depends()):
    return await service.all()
