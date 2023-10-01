import asyncio
import datetime

from sqlalchemy import (
    Table, Text, and_, or_, Column, DateTime, Integer, ForeignKey, select,
    TypeDecorator,
)

from sqlalchemy.orm import relationship, remote, declared_attr, declarative_base
from sqlalchemy.sql import func, cast
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncEngine

Base = declarative_base()

seconds_in_day = 24 * 60 * 60


class CustomDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if type(value) is str:
            return datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
        return value


class BaseTimePeriod:
    begin = Column(CustomDateTime, nullable=False)
    end = Column(CustomDateTime, nullable=True)

    @hybrid_property
    def duration(self):
        return (self.end - self.begin).seconds

    @duration.expression
    def duration(self):
        seconds = cast(
            seconds_in_day * (
                    func.julianday(self.end) - func.julianday(self.begin)),
            Integer
        )
        return select(func.coalesce(seconds, 0))


class PrimaryBegin(BaseTimePeriod):
    begin = Column(CustomDateTime, primary_key=True)


class SessionLike(BaseTimePeriod):
    @declared_attr
    def channel_id(self):
        return Column(Integer, ForeignKey('session.channel_id'),
                      primary_key=True, index=True)

    @declared_attr
    def member_id(self):
        return Column(Integer, ForeignKey("member.id"), primary_key=True)

    @declared_attr
    def begin(self):
        return Column(CustomDateTime, primary_key=True)


date_placeholder = func.date('now', 'localtime', '+1 month')

member_session = Table(
    "member_session",
    Base.metadata,  # noqa
    Column("member_id", ForeignKey("member.id"), primary_key=True),
    Column("channel_id", ForeignKey("session.channel_id"), primary_key=True),
)


class Activity(Base, PrimaryBegin):
    __tablename__ = 'activity'

    id = Column(
        Integer,
        ForeignKey('activity_info.app_id'),
        primary_key=True,
        index=True
    )
    member_id = Column(
        Integer,
        ForeignKey('member.id'),
        primary_key=True,
        index=True
    )

    info = relationship("ActivityInfo", lazy="selectin")


class Leadership(Base, SessionLike):
    __tablename__ = 'leadership'


class Prescence(Base, SessionLike):
    __tablename__ = 'prescence'


class Member(Base):
    __tablename__ = 'member'

    id = Column(Integer, primary_key=True, index=True)

    name = Column(Text)
    default_sess_name = Column(Text, default=None)

    sessions = relationship(
        "Session",
        secondary=member_session,
        back_populates='members',
        uselist=True,
        lazy='dynamic'
    )
    activities = relationship(
        "Activity",
        lazy='dynamic'
    )
    prescences = relationship("Prescence")


class Session(Base, BaseTimePeriod):
    __tablename__ = 'session'

    name = Column(Text)
    creator_id = Column(Integer)
    leader_id = Column(Integer)
    message_id = Column(Integer)

    channel_id = Column(Integer, primary_key=True, index=True)

    prescence = relationship("Prescence", lazy='selectin')

    leadership = relationship(
        "Leadership",
        uselist=True,
        lazy='subquery',
    )
    members = relationship(
        "Member",
        secondary=member_session,
        back_populates='sessions',
        uselist=True,
        lazy='subquery'
    )
    activities = relationship(
        'Activity',
        innerjoin=True,
        lazy='immediate',
        viewonly=True,
        uselist=True,
        order_by=Activity.begin,
        primaryjoin=  # noqa
        and_(
            channel_id == remote(member_session.c.channel_id),
            member_session.c.member_id == Member.id,
            Member.id == Activity.member_id,
            Prescence.member_id == Member.id,
            channel_id == Prescence.channel_id,
            or_(
                Activity.begin.between(
                    Prescence.begin,
                    func.coalesce(Prescence.end, date_placeholder)
                ),
                Activity.end.between(
                    Prescence.begin,
                    func.coalesce(Prescence.end, date_placeholder)
                )
            )
        )
    )


class ActivityInfo(Base):
    __tablename__ = 'activity_info'

    app_name = Column(Text)
    icon_url = Column(Text)

    app_id = Column(Integer, index=True, primary_key=True)

    role = relationship(
        "Role",
        back_populates="info",
        uselist=False,
        lazy='selectin'
    )


class Role(Base):
    __tablename__ = 'role'

    id = Column(Integer)
    info = relationship("ActivityInfo", lazy="selectin")

    app_id = Column(
        Integer,
        ForeignKey("activity_info.app_id"),
        primary_key=True
    )
    emoji = relationship(
        "Emoji",
        back_populates="role",
        lazy="selectin",
        cascade="all, delete",
        uselist=False
    )


class Emoji(Base):
    __tablename__ = 'emoji'

    id = Column(Integer)

    role_id = Column(Integer, ForeignKey("role.id"), primary_key=True)
    role = relationship("Role")


class FavoriteMusic(Base):
    __tablename__ = 'favorite_music'

    user_id = Column(
        Integer,
        ForeignKey('member.id'),
        primary_key=True,
        index=True
    )
    title = Column(Text)

    query = Column(Text, primary_key=True)
    counter = Column(Integer, default=1)


class SentMessage(Base):
    __tablename__ = 'sent_message'

    id = Column(Integer, primary_key=True, index=True)


class Guild(Base):
    __tablename__ = 'guild'

    id = Column(Integer, primary_key=True, index=True)

    create = relationship("Create", lazy="selectin", uselist=False)

    logger = relationship("Logger", lazy="selectin", uselist=False)
    command = relationship("Command", lazy="selectin", uselist=False)
    role_request = relationship("RoleRequest", lazy="selectin", uselist=False)

    idle_category = relationship("IdleCategory", lazy="selectin", uselist=False)
    playing_category = relationship("PlayingCategory", lazy="selectin",
                                    uselist=False)


class Logger(Base):
    __tablename__ = 'logger'

    id = Column(Integer, primary_key=True, index=True)

    guild_id = Column(Integer, ForeignKey("guild.id"), primary_key=True)


class Command(Base):
    __tablename__ = 'command'

    id = Column(Integer, primary_key=True,
                index=True)
    guild_id = Column(Integer, ForeignKey("guild.id"), primary_key=True)


class RoleRequest(Base):
    __tablename__ = 'role_request'

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guild.id"), primary_key=True)


class Create(Base):
    __tablename__ = 'create'

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guild.id"), primary_key=True)


class IdleCategory(Base):
    __tablename__ = 'idle_category'

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guild.id"), primary_key=True)


class PlayingCategory(Base):
    __tablename__ = 'playing_category'

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guild.id"), primary_key=True)


class SessionFabric:

    @staticmethod
    async def init_models(engine):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def __call__(self, session_maker: async_sessionmaker, engine: AsyncEngine):
        self.session_maker = session_maker
        try:
            asyncio.create_task(self.init_models(engine))
        except RuntimeError:
            asyncio.run(self.init_models(engine))
        return self.get_session

    async def get_session(self) -> AsyncSession:
        async with self.session_maker() as session:
            yield session


session_fabric = SessionFabric()
