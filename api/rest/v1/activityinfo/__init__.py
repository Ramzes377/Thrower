from fastapi import Depends, APIRouter

from .services import SrvActivityInfo
from ..schemas import ActivityInfo

router = APIRouter(prefix='/activityinfo', tags=['activityinfo'])


@router.get('/{app_id}', response_model=ActivityInfo)
def get(app_id: int, service: SrvActivityInfo = Depends()):
    return service.get(app_id)


@router.get('/all/', response_model=list[ActivityInfo])
def get_all(service: SrvActivityInfo = Depends()):
    return service.get_all()
