import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, relationship, backref

from api.rest.database import engine
from api.rest.v1.tables_mixins import BaseTimePeriod, PrimaryBegin, LeadershipLike

Base = declarative_base()

member_session = sa.Table(
    "member_session",
    Base.metadata,
    sa.Column("member_id", sa.ForeignKey("member.id"), primary_key=True),
    sa.Column("channel_id", sa.ForeignKey("session.channel_id"), primary_key=True),
)


class Member(Base):
    __tablename__ = 'member'

    id = sa.Column(sa.Integer, primary_key=True, index=True)

    name = sa.Column(sa.Text)
    default_sess_name = sa.Column(sa.Text, default=None)

    sessions = relationship("Session", secondary=member_session,
                            backref=backref('members', lazy='dynamic'),
                            lazy='dynamic')
    activities = relationship("Activity", lazy='dynamic')
    prescences = relationship("Prescence", back_populates="member")


class Session(Base, BaseTimePeriod):
    __tablename__ = 'session'

    channel_id = sa.Column(sa.Integer, primary_key=True, index=True)

    creator_id = sa.Column(sa.Integer)
    leader_id = sa.Column(sa.Integer)
    message_id = sa.Column(sa.Integer)
    name = sa.Column(sa.Text)

    prescence = relationship("Prescence")
    leadership = relationship("Leadership")


class Leadership(Base, LeadershipLike):
    __tablename__ = 'leadership'


class Prescence(Base, LeadershipLike):
    __tablename__ = 'prescence'
    member = relationship("Member", back_populates="prescences")


class ActivityInfo(Base):
    __tablename__ = 'activityinfo'

    app_id = sa.Column(sa.Integer, index=True, primary_key=True)

    app_name = sa.Column(sa.Text)
    icon_url = sa.Column(sa.Text)

    role = relationship("Role", back_populates="info")


class Activity(Base, PrimaryBegin):
    __tablename__ = 'activity'

    id = sa.Column(sa.Integer, sa.ForeignKey('activityinfo.app_id'), primary_key=True, index=True)
    member_id = sa.Column(sa.Integer, sa.ForeignKey('member.id'), primary_key=True, index=True)

    info = relationship("ActivityInfo")


class Role(Base):
    __tablename__ = 'role'

    app_id = sa.Column(sa.Integer, sa.ForeignKey("activityinfo.app_id"), primary_key=True)

    id = sa.Column(sa.Integer)

    info = relationship("ActivityInfo")
    emoji = relationship("Emoji", back_populates="role", cascade="all, delete")


class Emoji(Base):
    __tablename__ = 'emoji'

    role_id = sa.Column(sa.Integer, sa.ForeignKey("role.id"), primary_key=True)

    id = sa.Column(sa.Integer)

    role = relationship("Role")


class FavoriteMusic(Base):
    __tablename__ = 'favoritemusic'

    user_id = sa.Column(sa.Integer, sa.ForeignKey('member.id'), primary_key=True, index=True)
    query = sa.Column(sa.Text, primary_key=True)

    title = sa.Column(sa.Text)
    counter = sa.Column(sa.Integer)


Base.metadata.create_all(engine)
