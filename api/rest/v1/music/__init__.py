from fastapi import Depends, APIRouter

from .services import SrvFavoriteMusic
from .specifications import UserID
from ..dependencies import query_amount
from ..schemas import FavoriteMusic

router = APIRouter(prefix='/favoritemusic', tags=['favoritemusic'])


@router.get('/{user_id}', response_model=list[FavoriteMusic])
def get(user_id: UserID = Depends(), limit=Depends(query_amount), service: SrvFavoriteMusic = Depends()):
    return service.get(user_id, amount=limit)


@router.post('/', response_model=FavoriteMusic)
def post(data: FavoriteMusic, service: SrvFavoriteMusic = Depends()):
    return service.post(data)
