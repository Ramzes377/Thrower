from fastapi import Depends, APIRouter

from .services import SrvEmoji
from ..schemas import Emoji

router = APIRouter(prefix='/emoji', tags=['emoji'])


@router.get('/{emoji_id}', response_model=Emoji)
def emoji(emoji_id: int, service: SrvEmoji = Depends()):
    return service.get(emoji_id)


@router.post('/', response_model=Emoji)
def emoji(emojidata: Emoji, service: SrvEmoji = Depends()):
    return service.post(emojidata)


@router.get('/{emoji_id}/role', response_model=Emoji)
def get_role(emoji_id: int, service: SrvEmoji = Depends()):
    return service.get_role(emoji_id)
