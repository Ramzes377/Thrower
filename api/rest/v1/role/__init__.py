from fastapi import Depends, APIRouter

from .services import SrvRole
from ..schemas import Role, Emoji

router = APIRouter(prefix='/role', tags=['role'])


@router.get('/{role_id}', response_model=Role)
def role(role_id: int, service: SrvRole = Depends()):
    return service.get(role_id)


@router.get('/{role_id}/emoji/', response_model=Emoji)
def role(role_id: int, service: SrvRole = Depends()):
    return service.get_emoji(role_id)


@router.post('/', response_model=Role)
def role(roledata: Role, service: SrvRole = Depends()):
    return service.post(roledata)


@router.get('/by_app/{app_id}', response_model=Role)
def role(app_id: int, service: SrvRole = Depends()):
    return service.get_by_app(app_id)
