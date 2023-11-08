from api import crud_fabric, tables
from api.schemas import GuildChannels
from api.specification import GuildID

router = crud_fabric(
    table=tables.Guild,
    relative_path='guild',
    get_path='/{guild_id}',
    response_model=GuildChannels,
    specification=GuildID
)
