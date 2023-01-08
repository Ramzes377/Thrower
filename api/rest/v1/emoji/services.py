from api.rest.v1 import tables
from api.rest.v1.schemas import Emoji, Role

from api.rest.v1.base_service import BaseService


class SrvEmoji(BaseService):
    def _get(self, emoji_id: int):
        return (
            self._session.query(tables.Emoji)
            .filter_by(id=emoji_id)
        )

    def get(self, emoji_id: int) -> Emoji:
        return self._get(emoji_id).first()

    def post(self, emojidata: Emoji) -> tables.Emoji:
        emoji = tables.Emoji(**emojidata.dict())
        self.add_object(emoji)
        return emoji

    def get_role(self, emoji_id: int) -> Role:
        return (
            self._get(emoji_id)
            .join(tables.Role)
            .filter(tables.Emoji.role_id == tables.Role.id)
            .first()
        )
