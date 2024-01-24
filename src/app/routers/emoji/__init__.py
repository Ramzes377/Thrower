from fastapi import Depends

from src.utils import CrudType
from src.app import tables
from src.app.specification import EmojiID
from src.app.schemas import Emoji, Role
from src.app.service import crud_fabric

router, Service = crud_fabric(
    table=tables.Emoji,
    relative_path='emoji',
    get_path='/{emoji_id}',
    response_model=Emoji,
    specification=EmojiID,
    with_all=True,
    crud_type=CrudType.CR
)


@router.get('/{emoji_id}/role', response_model=Role)
async def get_emoji_role(
        emoji_id: EmojiID = Depends(),
        service: Service = Depends()
):
    emoji: tables.Emoji = await service.get(emoji_id)
    return emoji.role
