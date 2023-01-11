from api.rest.v1 import tables
from api.rest.v1.service import CRUD


class SrvRole(CRUD):
    table = tables.Role
