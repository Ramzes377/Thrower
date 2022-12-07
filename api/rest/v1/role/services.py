from api.rest.v1 import tables
from api.rest.v1.schemas import Role, Emoji

from api.rest.v1.base_service import BaseService


class SrvRole(BaseService):
    def _get(self, role_id: int) -> Role:
        return (
            self._session.query(tables.Role)
                .filter_by(id=role_id)
        )

    def get(self, role_id: int) -> Role:
        return self._get(role_id).first()

    def post(self, roledata: Role) -> tables.Role:
        role = tables.Role(**roledata.dict())
        self._db_add_obj(role)
        return role

    def get_emoji(self, role_id: int) -> Emoji:
        return (
            self._session.query(tables.Emoji)
                .join(self._get(role_id))
                .first()
        )

    def get_by_app(self, app_id: int) -> Role:
        return (
            self._session.query(tables.Role)
                .filter_by(app_id=app_id)
                .first()
        )