from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from .tables import Base as BaseTable


def row2dict(r: BaseTable):
    return {c.name: getattr(r, c.name) for c in r.__table__.columns}


def row2json(r: BaseTable):
    return jsonable_encoder(row2dict(r))


def modify_response(content: BaseTable):
    return JSONResponse(status_code=202, content=row2json(content))
