from datetime import datetime

from pydantic import BaseModel, NonNegativeInt


class EncoderBase(BaseModel):
    class Config:
        json_encoders = {
            datetime: str
        }
        from_attributes = True


class Role(EncoderBase):
    id: int
    app_id: int


class Emoji(EncoderBase):
    id: int
    role_id: int


class FavoriteMusic(EncoderBase):
    user_id: int
    query: str
    title: str | None = None
    counter: NonNegativeInt = None


class User(EncoderBase):
    id: int
    name: str
    default_sess_name: str | None = None


class ID(EncoderBase):
    id: int


class SessionLike(EncoderBase):
    member_id: int
    channel_id: int

    begin: datetime
    end: datetime | None = None


class Session(EncoderBase):
    channel_id: int
    name: str
    leader_id: int
    creator_id: int
    message_id: int
    begin: datetime
    end: datetime | None = None


class ActivityInfo(EncoderBase):
    app_id: int
    app_name: str
    icon_url: str


class Activity(EncoderBase):
    member_id: int
    id: int

    begin: datetime
    end: datetime | None = None


class IngameSeconds(BaseModel):
    app_id: int
    seconds: int


class DurationActivity(Activity):
    duration: int


class Prescence(SessionLike):
    end: datetime | None = None


class Leadership(SessionLike):
    member_id: int | None


class LeaderChange(BaseModel):
    channel_id: int
    member_id: int | None
    begin: datetime


class EndPrescence(EncoderBase):
    member_id: int
    channel_id: int
    end: datetime


class EndActivity(EncoderBase):
    member_id: int
    id: int
    end: datetime


class EndSession(EncoderBase):
    end: datetime


class GuildForeign(ID):
    guild_id: int
