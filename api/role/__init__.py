from fastapi import Depends, APIRouter, status

from .services import SrvRole
from api import tables
from api.schemas import Role, Emoji, ActivityInfo
from api.specification import RoleID, ActivityID

router = APIRouter(prefix='/role', tags=['role'])


@router.get('', response_model=list[Role])
async def all_roles(service: SrvRole = Depends()):
    return await service.all()


@router.post('', response_model=Role, status_code=status.HTTP_201_CREATED)
async def role(role: Role, service: SrvRole = Depends()):
    return await service.post(role)


@router.get('/by_app/{app_id}', response_model=Role)
async def role(app_id: ActivityID = Depends(), service: SrvRole = Depends()):
    return await service.get(app_id)


@router.delete('/{role_id}', status_code=status.HTTP_204_NO_CONTENT)
async def role(role_id: RoleID = Depends(), service: SrvRole = Depends()):
    return await service.delete(role_id)


@router.get('/{role_id}', response_model=Role)
async def role(role_id: RoleID = Depends(), service: SrvRole = Depends()):
    return await service.get(role_id)


@router.get('/{role_id}/emoji', response_model=Emoji)
async def role(role_id: RoleID = Depends(), service: SrvRole = Depends()):
    r: tables.Role = await service.get(role_id)
    return r.emoji


@router.get('/{role_id}/info', response_model=ActivityInfo)
async def role(role_id: RoleID = Depends(), service: SrvRole = Depends()):
    r: tables.Role = await service.get(role_id)
    return r.info
