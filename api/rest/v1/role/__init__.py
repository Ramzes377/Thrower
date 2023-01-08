from fastapi import Depends, APIRouter

from .services import SrvRole
from ..schemas import Role, Emoji, ActivityInfo

router = APIRouter(prefix='/role', tags=['role'])


@router.get('/{role_id}', response_model=Role)
def role(role_id: int, service: SrvRole = Depends()):
    return service.get(role_id)


@router.post('/', response_model=Role)
def role(roledata: Role, service: SrvRole = Depends()):
    return service.post(roledata)


@router.delete('/{role_id}')
def role(role_id: int, service: SrvRole = Depends()):
    return service.delete(role_id)


@router.get('/by_app/{app_id}', response_model=Role)
def role(app_id: int, service: SrvRole = Depends()):
    return service.get(app_id=app_id)


@router.get('/{role_id}/emoji/', response_model=Emoji)
def role(role_id: int, service: SrvRole = Depends()):
    return service.emoji(role_id)


@router.get('/{role_id}/info/', response_model=ActivityInfo)
def role(role_id: int, service: SrvRole = Depends()):
    return service.info(role_id)
