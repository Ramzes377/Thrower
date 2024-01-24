from src.utils import CrudType
from src.app import tables
from src.app.schemas import ActivityInfo
from src.app.specification import ActivityID
from src.app.service import crud_fabric

router, _ = crud_fabric(
    table=tables.ActivityInfo,
    relative_path='activity_info',
    get_path='/{app_id}',
    response_model=ActivityInfo,
    specification=ActivityID,
    with_all=True,
    crud_type=CrudType.CR
)
