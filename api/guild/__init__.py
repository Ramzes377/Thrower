from api import crud_fabric, tables
from api.schemas import GuildChannels
from api.specification import GuildID

router = crud_fabric(
    table=tables.Guild,
    prefix='guild',
    path='/{guild_id}',
    response_model=GuildChannels,
    specification=GuildID
)
