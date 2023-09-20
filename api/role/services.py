from api import tables
from api.service import CRUD


class SrvRole(CRUD):
    table = tables.Role
