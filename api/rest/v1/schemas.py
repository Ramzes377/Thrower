from datetime import datetime

from pydantic import BaseModel
from pydantic_sqlalchemy import sqlalchemy_to_pydantic

from api.rest.v1.tables import Member, Role, Emoji, ActivityInfo, FavoriteMusic, SentMessage

Role = sqlalchemy_to_pydantic(Role)
Emoji = sqlalchemy_to_pydantic(Emoji)
Member = sqlalchemy_to_pydantic(Member)
SentMessage = sqlalchemy_to_pydantic(SentMessage)
ActivityInfo = sqlalchemy_to_pydantic(ActivityInfo)
FavoriteMusic = sqlalchemy_to_pydantic(FavoriteMusic)


class EncoderBase(BaseModel):
    class Config:
        json_encoders = {
            datetime: lambda d: str(d)
        }
        orm_mode = True


class SessionLike(EncoderBase):
    member_id: int
    channel_id: int

    begin: datetime
    end: datetime | None


class Session(EncoderBase):
    channel_id: int
    name: str
    leader_id: int
    creator_id: int
    message_id: int
    begin: datetime
    end: datetime | None


class EndSession(EncoderBase):
    channel_id: int
    end: datetime


class Prescence(SessionLike):
    pass


class EndPrescence(EncoderBase):
    member_id: int
    channel_id: int
    end: datetime


class Leadership(SessionLike):
    member_id: int | None


class LeaderChange(BaseModel):
    channel_id: int
    member_id: int
    begin: datetime


class Activity(EncoderBase):
    member_id: int
    id: int

    begin: datetime
    end: datetime | None


class EndActivity(EncoderBase):
    member_id: int
    id: int
    end: datetime


class IngameSeconds(BaseModel):
    app_id: int
    seconds: int


class DurationActivity(Activity):
    duration: int
