import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declared_attr
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import cast


class BaseTimePeriod:
    begin = sa.Column(sa.DateTime, nullable=False)
    end = sa.Column(sa.DateTime, nullable=True)

    @hybrid_property
    def duration(cls):
        seconds_in_day = 24 * 60 * 60
        seconds = cast(
            seconds_in_day * (func.julianday(cls.end) - func.julianday(cls.begin)),
            sa.Integer
        )
        return seconds


class PrimaryBegin(BaseTimePeriod):
    begin = sa.Column(sa.DateTime, primary_key=True)


class LeadershipLike(BaseTimePeriod):
    @declared_attr
    def channel_id(cls):
        return sa.Column(sa.Integer, sa.ForeignKey('session.channel_id'), primary_key=True, index=True)

    @declared_attr
    def member_id(cls):
        return sa.Column(sa.Integer, sa.ForeignKey("member.id"), primary_key=True)

    @declared_attr
    def begin(cls):
        return sa.Column(sa.DateTime, primary_key=True)
