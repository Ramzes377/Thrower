from fastapi import Depends, APIRouter, status

from .services import SrvEmoji
from .specifications import EmojiID
from .. import tables
from ..schemas import Emoji, Role

router = APIRouter(prefix='/emoji', tags=['emoji'])


@router.get('/', response_model=list[Emoji])
def all_emojis(service: SrvEmoji = Depends()):
    return service.all()


@router.post('/', response_model=Emoji, status_code=status.HTTP_201_CREATED)
def create_emoji(emoji: Emoji, service: SrvEmoji = Depends()):
    return service.post(emoji)


@router.get('/{emoji_id}', response_model=Emoji)
def get_emoji(emoji_id: EmojiID = Depends(), service: SrvEmoji = Depends()):
    return service.get(emoji_id)


@router.get('/{emoji_id}/role', response_model=Role)
def get_role(emoji_id: EmojiID = Depends(), service: SrvEmoji = Depends()):
    emoji: tables.Emoji = service.get(emoji_id)
    return emoji.role
