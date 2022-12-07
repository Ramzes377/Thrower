from fastapi import Depends, APIRouter

from api.rest.v1.music.services import SrvFavoriteMusic
from ..schemas import FavoriteMusic

router = APIRouter(prefix='/favoritemusic', tags=['favoritemusic'])


@router.get('/{user_id}', response_model=list[FavoriteMusic])
def get(user_id: int, service: SrvFavoriteMusic = Depends()):
    return service.get(user_id)


@router.post('/', response_model=FavoriteMusic)
def post(data: FavoriteMusic, service: SrvFavoriteMusic = Depends()):
    return service.post(data)
