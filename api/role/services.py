from api import tables
from api.service import CRUD
from api.specification import Specification


class SrvRole(CRUD):
    table = tables.Role

    def get(self, app_id: Specification, *args, **kwargs):
        if args:
            guild_id = args[0]
            return super().get(app_id, guild_id=guild_id)
        return super().get(app_id)
