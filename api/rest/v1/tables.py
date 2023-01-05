from sqlalchemy import Table, Column, Integer, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, backref

from api.rest.database import engine
from api.rest.v1.tables_mixins import BaseTimePeriod, PrimaryBegin, LeadershipLike

Base = declarative_base()

member_session = Table(
    "member_session",
    Base.metadata,
    Column("member_id", ForeignKey("member.id"), primary_key=True),
    Column("channel_id", ForeignKey("session.channel_id"), primary_key=True),
)


class Member(Base):
    __tablename__ = 'member'

    id = Column(Integer, primary_key=True, index=True)

    name = Column(Text)
    default_sess_name = Column(Text, default=None)

    sessions = relationship("Session", secondary=member_session,
                            backref=backref('members', lazy='dynamic'),
                            lazy='dynamic')
    activities = relationship("Activity", lazy='dynamic')
    prescences = relationship("Prescence", back_populates="member")


class Session(Base, BaseTimePeriod):
    __tablename__ = 'session'

    channel_id = Column(Integer, primary_key=True, index=True)

    creator_id = Column(Integer)
    leader_id = Column(Integer)
    message_id = Column(Integer)
    name = Column(Text)

    prescence = relationship("Prescence")
    leadership = relationship("Leadership")


class Leadership(Base, LeadershipLike):
    __tablename__ = 'leadership'


class Prescence(Base, LeadershipLike):
    __tablename__ = 'prescence'
    member = relationship("Member", back_populates="prescences")


class ActivityInfo(Base):
    __tablename__ = 'activityinfo'

    app_id = Column(Integer, index=True, primary_key=True)

    app_name = Column(Text)
    icon_url = Column(Text)

    role = relationship("Role", back_populates="info")


class Activity(Base, PrimaryBegin):
    __tablename__ = 'activity'

    id = Column(Integer, ForeignKey('activityinfo.app_id'), primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey('member.id'), primary_key=True, index=True)

    info = relationship("ActivityInfo")


class Role(Base):
    __tablename__ = 'role'

    app_id = Column(Integer, ForeignKey("activityinfo.app_id"), primary_key=True)

    id = Column(Integer)

    info = relationship("ActivityInfo")
    emoji = relationship("Emoji", back_populates="role", cascade="all, delete")


class Emoji(Base):
    __tablename__ = 'emoji'

    role_id = Column(Integer, ForeignKey("role.id"), primary_key=True)

    id = Column(Integer)

    role = relationship("Role")


class FavoriteMusic(Base):
    __tablename__ = 'favoritemusic'

    user_id = Column(Integer, ForeignKey('member.id'), primary_key=True, index=True)
    query = Column(Text, primary_key=True)

    title = Column(Text)
    counter = Column(Integer)


Base.metadata.create_all(engine)
