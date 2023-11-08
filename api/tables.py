import asyncio
import datetime
from typing import Union

from sqlalchemy import (
    Table, Text, and_, or_, Column, DateTime, Integer, ForeignKey, select,
    TypeDecorator, JSON, Engine, BigInteger
)

from sqlalchemy.dialects import mysql
from sqlalchemy.orm import relationship, remote, declared_attr, \
    declarative_base, sessionmaker
from sqlalchemy.sql import func, cast
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, \
    AsyncEngine, create_async_engine

Base = declarative_base()

seconds_in_day = 24 * 60 * 60

IntegerVariant = BigInteger().with_variant(Integer, "sqlite")


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
            IntegerVariant
        )
        return select(func.coalesce(seconds, 0))


class PrimaryBegin(BaseTimePeriod):
    begin = Column(CustomDateTime, primary_key=True)


class SessionLike(BaseTimePeriod):
    @declared_attr
    def channel_id(self):
        return Column(IntegerVariant, ForeignKey('session.channel_id'),
                      primary_key=True, index=True)

    @declared_attr
    def member_id(self):
        return Column(
            IntegerVariant,
            ForeignKey("member.id"),
            primary_key=True,
            index=True
        )

    @declared_attr
    def begin(self):
        return Column(CustomDateTime, primary_key=True)


member_session = Table(
    "member_session",
    Base.metadata,  # noqa
    Column("member_id", ForeignKey("member.id"), primary_key=True, index=True),
    Column("channel_id", ForeignKey("session.channel_id"), primary_key=True,
           index=True),
)


class Activity(Base, PrimaryBegin):
    __tablename__ = 'activity'

    id = Column(
        IntegerVariant,
        ForeignKey('activity_info.app_id'),
        primary_key=True,
        index=True
    )
    member_id = Column(
        IntegerVariant,
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

    id = Column(IntegerVariant, primary_key=True, index=True)

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
    creator_id = Column(IntegerVariant)
    leader_id = Column(IntegerVariant)
    message_id = Column(IntegerVariant)

    channel_id = Column(IntegerVariant, primary_key=True, index=True)

    prescence = relationship("Prescence", lazy='selectin')

    leadership = relationship(
        "Leadership",
        uselist=True,
        lazy='subquery',
    )
    members = relationship(
        "Member",
        secondary='member_session',
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
                and_(
                    Prescence.end.isnot(None),
                    or_(
                        Activity.begin.between(Prescence.begin, Prescence.end),
                        and_(
                            Activity.end.is_not(None),
                            Activity.end.between(Prescence.begin, Prescence.end)
                        )
                    )
                ),
                and_(
                    Prescence.end.is_(None),
                    Activity.begin > Prescence.begin
                )
            )
        )
    )


class ActivityInfo(Base):
    __tablename__ = 'activity_info'

    app_name = Column(Text)
    icon_url = Column(Text)

    app_id = Column(IntegerVariant, index=True, primary_key=True)

    role = relationship(
        "Role",
        back_populates="info",
        uselist=False,
        lazy='selectin'
    )


class Role(Base):
    __tablename__ = 'role'

    id = Column(IntegerVariant, index=True)
    info = relationship("ActivityInfo", lazy="selectin")

    app_id = Column(
        IntegerVariant,
        ForeignKey("activity_info.app_id"),
        primary_key=True
    )
    guild_id = Column(
        IntegerVariant,
        ForeignKey('guild.id'),
        primary_key=True,
        default=257878464667844618
    )

    emoji = relationship(
        "Emoji",
        back_populates="role",
        lazy="selectin",
        cascade="all, delete",
        uselist=False
    )
    guild = relationship(
        "Guild",
        lazy="selectin",
        uselist=False
    )


class Emoji(Base):
    __tablename__ = 'emoji'

    id = Column(IntegerVariant, index=True)

    role_id = Column(IntegerVariant, ForeignKey("role.id"),
                     primary_key=True,
                     index=True)
    role = relationship("Role")


class FavoriteMusic(Base):
    __tablename__ = 'favorite_music'

    user_id = Column(
        IntegerVariant,
        ForeignKey('member.id'),
        primary_key=True,
        index=True
    )
    title = Column(Text)

    query = Column(
        Text().with_variant(mysql.VARCHAR(length=512, charset="utf8"),
                            "mysql"),
        primary_key=True
    )
    counter = Column(IntegerVariant, default=1)


class SentMessage(Base):
    __tablename__ = 'sent_message'

    id = Column(IntegerVariant, primary_key=True, index=True)
    guild_id = Column(IntegerVariant, ForeignKey('guild.id'))


class Guild(Base):
    __tablename__ = 'guild'

    id = Column(IntegerVariant, primary_key=True, index=True)

    initialized_channels = Column(JSON, nullable=False, default={})


class SessionFabric:

    def init_tables(self):
        if self.is_async:
            async def init_models(_engine):
                async with _engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

            try:
                asyncio.create_task(init_models(self.engine))
            except RuntimeError:
                asyncio.run(init_models(self.engine))

        else:
            Base.metadata.create_all(bind=self.engine)

    def __init__(self,
                 session_maker: Union[async_sessionmaker, sessionmaker],
                 engine: Union[AsyncEngine, Engine],
                 is_async: bool = True):
        self.engine = engine
        self.session_maker = session_maker

        self.is_async = is_async

        self.init_tables()

    @staticmethod
    def _build(
            db_uri: str,
            connect_args: dict | None = None,
    ) -> tuple[AsyncEngine, async_sessionmaker]:
        if connect_args is None:
            connect_args = {}

        engine = create_async_engine(
            db_uri,
            echo=False,
            pool_pre_ping=True,
            connect_args=connect_args
        )
        session_maker = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        return engine, session_maker

    @classmethod
    def build(
            cls,
            db_uri: str,
            connect_args: dict | None = None,
    ):
        engine, session_maker = cls._build(
            db_uri=db_uri,
            connect_args=connect_args,
        )
        self = cls(
            engine=engine,
            session_maker=session_maker,
        )

        return self.get_session

    async def get_session(self) -> AsyncSession:
        if self.is_async:
            async with self.session_maker() as session:
                yield session
        else:
            with self.session_maker() as session:
                yield session
