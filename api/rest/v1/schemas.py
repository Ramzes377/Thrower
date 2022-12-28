from pydantic import BaseModel
from pydantic_sqlalchemy import sqlalchemy_to_pydantic

from api.rest.v1.tables import Member, Session, Activity, Prescence, Leadership, Role, Emoji, ActivityInfo, FavoriteMusic


Role = sqlalchemy_to_pydantic(Role)
Emoji = sqlalchemy_to_pydantic(Emoji)
Member = sqlalchemy_to_pydantic(Member)
Session = sqlalchemy_to_pydantic(Session)
Activity = sqlalchemy_to_pydantic(Activity)
Prescence = sqlalchemy_to_pydantic(Prescence)
Leadership = sqlalchemy_to_pydantic(Leadership)
ActivityInfo = sqlalchemy_to_pydantic(ActivityInfo)
FavoriteMusic = sqlalchemy_to_pydantic(FavoriteMusic)


class IngameSeconds(BaseModel):
    app_id: int
    seconds: int