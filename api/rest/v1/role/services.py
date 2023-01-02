from fastapi import HTTPException

from api.rest.v1 import tables
from api.rest.v1.schemas import Role, Emoji, ActivityInfo

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
        return self.get(role_id).emoji[0]

    def get_by_app(self, app_id: int) -> Role:
        return (
            self._session.query(tables.Role)
                .filter_by(app_id=app_id)
                .first()
        )

    def get_info(self, role_id: int) -> ActivityInfo:
        return self.get(role_id).info

    def delete(self, role_id: int):
        role = self.get(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        self._session.delete(role)
        self._session.commit()
        return {"ok": True}