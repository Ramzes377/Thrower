from api import tables
from api.schemas import GuildForeign, ID
from api.service import create_simple_crud

prefixes_tables = [
    ('guild', tables.Guild),
    ('logger', tables.Logger),
    ('command', tables.Command),
    ('role_request', tables.RoleRequest),
    ('create_channel', tables.Create),
    ('idle_category', tables.IdleCategory),
    ('playing_category', tables.PlayingCategory),
]

routers = [
]

for prefix, table in prefixes_tables:
    routers.append(
        create_simple_crud(
            table=table,
            endpoint_prefix=prefix,
            path='id',
            response_model=GuildForeign if prefix != 'guild' else ID,
            include_in_schema=True
        )
    )
