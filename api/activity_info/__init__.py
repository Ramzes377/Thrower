from api.schemas import ActivityInfo
from api.specification import ActivityID
from utils import CrudType
from .. import crud_fabric, tables

router = crud_fabric(
    table=tables.ActivityInfo,
    relative_path='activity_info',
    get_path='/{app_id}',
    response_model=ActivityInfo,
    specification=ActivityID,
    with_all=True,
    crud_type=CrudType.CR
)
