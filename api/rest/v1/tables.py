import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, relationship, backref

from api.rest.database import engine

Base = declarative_base()

member_session = sa.Table(
    "member_session",
    Base.metadata,
    sa.Column("member_id", sa.ForeignKey("member.id"), primary_key=True),
    sa.Column("channel_id", sa.ForeignKey("session.channel_id"), primary_key=True),
)


class Member(Base):
    __tablename__ = 'member'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(length=255))
    default_sess_name = sa.Column(sa.String(length=255), default=None)

    activities = relationship("Activity")
    sessions = relationship("Session", secondary=member_session,
                            backref=backref('members', lazy='dynamic'),
                            lazy='dynamic')
    prescences = relationship("Prescence", back_populates="member")


class Session(Base):
    __tablename__ = 'session'

    channel_id = sa.Column(sa.Integer, primary_key=True)
    creator_id = sa.Column(sa.Integer)
    leader_id = sa.Column(sa.Integer)
    message_id = sa.Column(sa.Integer)
    name = sa.Column(sa.String(length=255))

    begin = sa.Column(sa.DateTime, nullable=False)
    end = sa.Column(sa.DateTime)

    prescence = relationship("Prescence")
    leadership = relationship("Leadership")


class Prescence(Base):
    __tablename__ = 'prescence'

    channel_id = sa.Column(sa.Integer, sa.ForeignKey('session.channel_id'), primary_key=True)
    member_id = sa.Column(sa.Integer, sa.ForeignKey("member.id"), primary_key=True)
    begin = sa.Column(sa.DateTime, primary_key=True)
    end = sa.Column(sa.DateTime, nullable=True)

    member = relationship("Member", back_populates="prescences")


class Leadership(Base):
    __tablename__ = 'leadership'

    member_id = sa.Column(sa.Integer, sa.ForeignKey("member.id"), primary_key=True)
    channel_id = sa.Column(sa.Integer, sa.ForeignKey("session.channel_id"), primary_key=True)
    begin = sa.Column(sa.DateTime, primary_key=True)
    end = sa.Column(sa.DateTime, nullable=True)


class Activity(Base):
    __tablename__ = 'activity'

    id = sa.Column(sa.Integer, sa.ForeignKey('activityinfo.app_id'), primary_key=True)
    member_id = sa.Column(sa.Integer, sa.ForeignKey('member.id'), primary_key=True)

    begin = sa.Column(sa.DateTime, primary_key=True)
    end = sa.Column(sa.DateTime)

    role = relationship("Role")
    info = relationship("ActivityInfo")


class ActivityInfo(Base):
    __tablename__ = 'activityinfo'

    app_name = sa.Column(sa.Text)
    icon_url = sa.Column(sa.Text)

    app_id = sa.Column(sa.Integer, sa.ForeignKey("role.app_id"), primary_key=True)


class Role(Base):
    __tablename__ = 'role'

    id = sa.Column(sa.Integer)
    app_id = sa.Column(sa.Integer, sa.ForeignKey("activity.id"), primary_key=True)
    emoji = relationship("Emoji")


class Emoji(Base):
    __tablename__ = 'emoji'

    id = sa.Column(sa.Integer)
    role_id = sa.Column(sa.Integer, sa.ForeignKey("role.id"), primary_key=True)


class FavoriteMusic(Base):
    __tablename__ = 'favoritemusic'

    title = sa.Column(sa.Text)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('member.id'), primary_key=True)
    query = sa.Column(sa.Text, primary_key=True)
    counter = sa.Column(sa.Integer)


Base.metadata.create_all(engine)
