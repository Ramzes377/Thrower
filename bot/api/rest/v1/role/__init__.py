from fastapi import Depends, APIRouter, status

from .services import SrvRole
from .. import tables
from ..schemas import Role, Emoji, ActivityInfo
from ..specifications import RoleID, ActivityID

router = APIRouter(prefix='/role', tags=['role'])


@router.get('/', response_model=list[Role])
def all_roles(service: SrvRole = Depends()):
    return service.all()


@router.post('/', response_model=Role, status_code=status.HTTP_201_CREATED)
def role(role: Role, service: SrvRole = Depends()):
    return service.post(role)


@router.get('/by_app/{app_id}', response_model=Role)
def role(app_id: ActivityID = Depends(), service: SrvRole = Depends()):
    return service.get(app_id)


@router.delete('/{role_id}', status_code=status.HTTP_204_NO_CONTENT)
def role(role_id: RoleID = Depends(), service: SrvRole = Depends()):
    return service.delete(role_id)


@router.get('/{role_id}', response_model=Role)
def role(role_id: RoleID = Depends(), service: SrvRole = Depends()):
    return service.get(role_id)


@router.get('/{role_id}/emoji/', response_model=Emoji)
def role(role_id: RoleID = Depends(), service: SrvRole = Depends()):
    r: tables.Role = service.get(role_id)
    return r.emoji


@router.get('/{role_id}/info/', response_model=ActivityInfo)
def role(role_id: RoleID = Depends(), service: SrvRole = Depends()):
    r: tables.Role = service.get(role_id)
    return r.info
