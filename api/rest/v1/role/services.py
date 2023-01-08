from fastapi import HTTPException, status

from api.rest.v1 import tables
from api.rest.v1.schemas import Role, Emoji, ActivityInfo

from api.rest.v1.base_service import BaseService


class SrvRole(BaseService):
    def _get(self, role_id: int = None, app_id: int = None):
        role = None
        query = self._session.query(tables.Role)

        if role_id is not None:
            role = query.filter_by(id=role_id)
        elif app_id is not None:
            role = query.filter_by(app_id=app_id)

        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return role

    def get(self, role_id: int = None, app_id: int = None) -> Role:
        return self._get(role_id, app_id).first()

    def post(self, roledata: Role) -> tables.Role:
        role = tables.Role(**roledata.dict())
        self.add_object(role)
        return role

    def emoji(self, role_id: int) -> Emoji:
        return self.get(role_id).emoji[0]

    def info(self, role_id: int) -> ActivityInfo:
        return self.get(role_id).info

    def delete(self, role_id: int):
        role = self.get(role_id)
        self._session.delete(role)
        self._session.commit()
        return {"ok": True}
