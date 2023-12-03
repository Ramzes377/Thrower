from src.app import tables
from src.app.service import crud_fabric
from src.app.schemas import GuildChannels
from src.app.specification import GuildID

router, _ = crud_fabric(
    table=tables.Guild,
    relative_path='guild',
    get_path='/{guild_id}',
    response_model=GuildChannels,
    specification=GuildID
)
