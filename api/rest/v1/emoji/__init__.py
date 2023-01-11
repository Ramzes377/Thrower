from fastapi import Depends, APIRouter

from .services import SrvEmoji
from .specifications import EmojiID
from ..schemas import Emoji, Role

router = APIRouter(prefix='/emoji', tags=['emoji'])


@router.get('/{emoji_id}', response_model=Emoji)
def emoji(emoji_id: EmojiID = Depends(), service: SrvEmoji = Depends()):
    return service.get(emoji_id)


@router.post('/', response_model=Emoji)
def emoji(emojidata: Emoji, service: SrvEmoji = Depends()):
    return service.post(emojidata)


@router.get('/{emoji_id}/role', response_model=Role)
def get_role(emoji_id: EmojiID = Depends(), service: SrvEmoji = Depends()):
    return service.get(emoji_id).role
