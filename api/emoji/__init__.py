from fastapi import Depends, APIRouter, status

from .services import SrvEmoji
from api.specification import EmojiID
from api import tables
from api.schemas import Emoji, Role

router = APIRouter(prefix='/emoji', tags=['emoji'])


@router.get('', response_model=list[Emoji])
async def all_emojis(service: SrvEmoji = Depends()):
    return await service.all()


@router.post('', response_model=Emoji, status_code=status.HTTP_201_CREATED)
async def create_emoji(emoji: Emoji, service: SrvEmoji = Depends()):
    return await service.post(emoji)


@router.get('/{emoji_id}', response_model=Emoji)
async def get_emoji(emoji_id: EmojiID = Depends(), service: SrvEmoji = Depends()):
    return await service.get(emoji_id)


@router.get('/{emoji_id}/role', response_model=Role)
async def get_role(emoji_id: EmojiID = Depends(), service: SrvEmoji = Depends()):
    emoji: tables.Emoji = await service.get(emoji_id)
    return emoji.role
