from sqlalchemy import Column, DateTime, Integer, ForeignKey
from sqlalchemy.orm import declared_attr
from sqlalchemy.sql import func, cast
from sqlalchemy.ext.hybrid import hybrid_property

seconds_in_day = 24 * 60 * 60


class BaseTimePeriod:
    begin = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=True)

    @hybrid_property
    def duration(self):
        seconds = cast(
            seconds_in_day * (func.julianday(self.end) - func.julianday(self.begin)),
            Integer
        )
        return func.coalesce(seconds, 0)


class PrimaryBegin(BaseTimePeriod):
    begin = Column(DateTime, primary_key=True)


# noinspection PyMethodParameters
class SessionLike(BaseTimePeriod):
    @declared_attr
    def channel_id(cls):
        return Column(Integer, ForeignKey('session.channel_id'), primary_key=True, index=True)

    @declared_attr
    def member_id(cls):
        return Column(Integer, ForeignKey("member.id"), primary_key=True)

    @declared_attr
    def begin(cls):
        return Column(DateTime, primary_key=True)
