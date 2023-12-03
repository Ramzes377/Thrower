from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, PositiveInt


class Role(BaseModel):
    id: int
    app_id: int
    guild_id: int


class Emoji(BaseModel):
    id: int
    role_id: int


class FavoriteMusic(BaseModel):
    user_id: int
    query: str
    title: Optional[str] = None
    counter: Optional[PositiveInt] = None


class User(BaseModel):
    id: int
    name: str
    default_sess_name: Optional[str] = None


class GuildForeign(BaseModel):
    id: int
    guild_id: int


class Session(BaseModel):
    channel_id: int
    name: str
    leader_id: int = None
    creator_id: int
    message_id: int
    begin: datetime
    end: Optional[datetime] = None


class ActivityInfo(BaseModel):
    app_id: int
    app_name: str
    icon_url: str


class Activity(BaseModel):
    member_id: int
    id: int

    begin: datetime
    end: Optional[datetime] = None


class SentMessage(BaseModel):
    id: int
    guild_id: int
    channel_id: Optional[int] = None


class DurationActivity(Activity):
    duration: int


class SessionLike(BaseModel):
    member_id: Optional[int] = None
    channel_id: int
    begin: Optional[datetime] = None
    end: Optional[datetime] = None


class EndActivity(BaseModel):
    id: int
    member_id: int
    end: datetime


class GuildChannels(BaseModel):
    id: int
    initialized_channels: dict


class IngameSeconds(BaseModel):
    app_id: int
    seconds: int


class AnyFields(BaseModel):
    model_config = ConfigDict(extra="allow")

    # fields for type hints
    id: Optional[int] = None
