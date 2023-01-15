from fastapi import Depends, APIRouter

from .services import SrvEmoji
from .specifications import EmojiID
from ..schemas import Emoji, Role
from .. import tables

router = APIRouter(prefix='/emoji', tags=['emoji'])


@router.get('/', response_model=list[Emoji])
def all_emojis(service: SrvEmoji = Depends()):
    return service.all()


@router.post('/', response_model=Emoji)
def create_emoji(emoji: Emoji, service: SrvEmoji = Depends()):
    return service.post(emoji)


@router.get('/{emoji_id}', response_model=Emoji)
def get_emoji(emoji_id: EmojiID = Depends(), service: SrvEmoji = Depends()):
    return service.get(emoji_id)


@router.get('/{emoji_id}/role', response_model=Role)
def get_role(emoji_id: EmojiID = Depends(), service: SrvEmoji = Depends()):
    emoji: tables.Emoji = service.get(emoji_id)
    return emoji.role
