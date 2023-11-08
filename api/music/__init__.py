from fastapi import Depends, APIRouter, status

from .services import SrvFavoriteMusic
from api.specification import MusicUserID
from api.dependencies import limit
from api.schemas import FavoriteMusic

router = APIRouter(prefix='/favorite_music', tags=['favorite_music'])


@router.get('/{user_id}', response_model=list[FavoriteMusic])
async def get(
    user_id: MusicUserID = Depends(),
    _limit: int = Depends(limit),
    service: SrvFavoriteMusic = Depends()
):
    return await service.first_of_all(user_id, amount=_limit)


@router.post('', response_model=FavoriteMusic,
             status_code=status.HTTP_201_CREATED)
async def post(data: FavoriteMusic, service: SrvFavoriteMusic = Depends()):
    return await service.post(data)
