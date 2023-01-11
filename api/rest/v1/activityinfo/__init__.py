from fastapi import Depends, APIRouter

from .services import SrvActivityInfo
from ..specifications import ActivityID
from ..schemas import ActivityInfo


router = APIRouter(prefix='/activityinfo', tags=['activityinfo'])


@router.get('/{app_id}', response_model=ActivityInfo)
def get(app_id: ActivityID = Depends(), service: SrvActivityInfo = Depends()):
    return service.get(app_id)


@router.get('/', response_model=list[ActivityInfo])
def get_all(service: SrvActivityInfo = Depends()):
    return service.all()
