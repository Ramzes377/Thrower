from fastapi import Depends, APIRouter, status

from .services import SrvActivityInfo
from ..specifications import ActivityID
from ..schemas import ActivityInfo


router = APIRouter(prefix='/activityinfo', tags=['activityinfo'])


@router.post('/', response_model=ActivityInfo, status_code=status.HTTP_201_CREATED)
def post(activity_info: ActivityInfo, service: SrvActivityInfo = Depends()):
    return service.post(activity_info)


@router.get('/{app_id}', response_model=ActivityInfo)
def get(app_id: ActivityID = Depends(), service: SrvActivityInfo = Depends()):
    return service.get(app_id)


@router.get('/', response_model=list[ActivityInfo])
def get_all(service: SrvActivityInfo = Depends()):
    return service.all()
