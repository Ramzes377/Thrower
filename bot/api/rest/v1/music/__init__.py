from fastapi import Depends, APIRouter, status

from .services import SrvFavoriteMusic
from .specifications import UserID
from ..dependencies import limit
from ..schemas import FavoriteMusic

router = APIRouter(prefix='/favoritemusic', tags=['favoritemusic'])


@router.get('/{user_id}', response_model=list[FavoriteMusic])
def get(user_id: UserID = Depends(), limit=Depends(limit), service: SrvFavoriteMusic = Depends()):
    return service.get(user_id, amount=limit)


@router.post('/', response_model=FavoriteMusic, status_code=status.HTTP_201_CREATED)
def post(data: FavoriteMusic, service: SrvFavoriteMusic = Depends()):
    return service.post(data)
