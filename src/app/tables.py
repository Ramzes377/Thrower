import asyncio
from datetime import datetime
from contextlib import suppress
from functools import partial
from typing import Union, Generator, Optional, Callable

from sqlalchemy import (
    Text, and_, or_, DateTime, Integer, ForeignKey,
    JSON, Engine, BigInteger, UniqueConstraint, create_engine, TypeDecorator
)
from sqlalchemy.exc import IllegalStateChangeError
from sqlalchemy.ext.asyncio import (AsyncSession, AsyncEngine,
                                    async_sessionmaker, create_async_engine)
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import (relationship, remote, sessionmaker, mapped_column,
                            Mapped)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()

IntegerVariant = BigInteger().with_variant(Integer, 'sqlite')
mapped_integer = partial(mapped_column, IntegerVariant)


class CustomDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if type(value) is str:
            return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
        return value


class BaseTimePeriod:
    begin: Mapped[datetime] = mapped_column(CustomDateTime, nullable=False)
    end: Mapped[datetime] = mapped_column(CustomDateTime, nullable=True)

    @hybrid_property
    def duration(self):
        return (self.end - self.begin).seconds


class PrimaryBegin(BaseTimePeriod):
    begin: Mapped[datetime] = mapped_column(CustomDateTime, primary_key=True)


class SessionLike(BaseTimePeriod):
    __abstract__ = True

    channel_id: Mapped[int] = mapped_integer(
        ForeignKey('session.channel_id'),
        primary_key=True,
        index=True
    )
    member_id: Mapped[int] = mapped_integer(
        ForeignKey('member.id'),
        primary_key=True,
        index=True
    )
    begin: Mapped[datetime] = mapped_column(CustomDateTime, primary_key=True)


class Activity(Base, PrimaryBegin):
    __tablename__ = 'activity'

    id: Mapped[int] = mapped_column(
        ForeignKey('activity_info.app_id'),
        primary_key=True,
        index=True
    )
    member_id: Mapped[int] = mapped_column(
        ForeignKey('member.id'),
        primary_key=True,
        index=True
    )

    info = relationship('ActivityInfo', lazy='selectin')


class Leadership(Base, SessionLike):
    __tablename__ = 'leadership'


class Prescence(Base, SessionLike):
    __tablename__ = 'prescence'


class MemberSessionAssociation(Base):
    __tablename__ = 'member_session'
    __table_args__ = (
        UniqueConstraint(
            'member_id',
            'channel_id',
            name='idx_unique_member_session'
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    member_id: Mapped[int] = mapped_column(
        ForeignKey('member.id'),
        index=True,
    )
    channel_id: Mapped[int] = mapped_column(
        ForeignKey('session.channel_id'),
        index=True,
    )


class Member(Base):
    __tablename__ = 'member'

    id: Mapped[int] = mapped_integer(primary_key=True, index=True)

    name: Mapped[str]
    default_sess_name: Mapped[Optional[str]]

    sessions: Mapped[list['Session']] = relationship(
        'Session',
        secondary='member_session',
        back_populates='members',
        uselist=True,
        lazy='dynamic'
    )
    activities: Mapped[list['Activity']] = relationship(
        'Activity',
        lazy='selectin'
    )
    prescences: Mapped[list['Prescence']] = relationship('Prescence')


class Session(Base, BaseTimePeriod):
    __tablename__ = 'session'

    name: Mapped[str]
    creator_id: Mapped[int] = mapped_integer()
    leader_id: Mapped[int] = mapped_integer()
    message_id: Mapped[int] = mapped_integer()

    channel_id: Mapped[int] = mapped_integer(primary_key=True, index=True)

    prescence: Mapped[list['Prescence']] = relationship(
        'Prescence',
        lazy='selectin'
    )

    leadership: Mapped[list['Leadership']] = relationship(
        'Leadership',
        uselist=True,
        lazy='selectin',
    )
    members: Mapped[list['Member']] = relationship(
        'Member',
        secondary='member_session',
        back_populates='sessions',
        uselist=True,
        lazy='selectin',
        innerjoin=True,
    )
    activities: Mapped[list['Activity']] = relationship(
        'Activity',
        innerjoin=True,
        lazy='immediate',
        viewonly=True,
        uselist=True,
        order_by=Activity.begin,
        primaryjoin=  # noqa
        and_(
            channel_id == remote(MemberSessionAssociation.channel_id),
            MemberSessionAssociation.member_id == Member.id,
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

    app_id: Mapped[int] = mapped_integer(index=True, primary_key=True)

    app_name: Mapped[str]
    icon_url: Mapped[str]

    role: Mapped['Role'] = relationship(
        'Role',
        back_populates='info',
        uselist=False,
        lazy='selectin'
    )


class Role(Base):
    __tablename__ = 'role'

    id: Mapped[int] = mapped_integer(index=True)
    app_id: Mapped[int] = mapped_integer(
        ForeignKey('activity_info.app_id'),
        primary_key=True
    )
    guild_id: Mapped[int] = mapped_integer(
        ForeignKey('guild.id'),
        primary_key=True,
        nullable=False,
        server_default='257878464667844618'
    )

    info: Mapped['ActivityInfo'] = relationship(
        'ActivityInfo',
        lazy='selectin',
        uselist=False
    )
    emoji: Mapped['Emoji'] = relationship(
        'Emoji',
        back_populates='role',
        lazy='selectin',
        cascade='all, delete',
        uselist=False
    )
    guild: Mapped['Guild'] = relationship(
        'Guild',
        lazy='selectin',
        uselist=False
    )


class Emoji(Base):
    __tablename__ = 'emoji'

    id: Mapped[int] = mapped_integer(index=True)

    role_id: Mapped[int] = mapped_integer(
        ForeignKey('role.id'),
        primary_key=True,
        index=True
    )
    role: Mapped['Role'] = relationship('Role')


class FavoriteMusic(Base):
    __tablename__ = 'favorite_music'

    user_id: Mapped[int] = mapped_integer(
        ForeignKey('member.id'),
        primary_key=True,
        index=True
    )
    title: Mapped[str]

    query: Mapped[str] = mapped_column(
        Text().with_variant(mysql.VARCHAR(length=512, charset='utf8'),
                            'mysql'),
        primary_key=True
    )
    counter: Mapped[int] = mapped_integer(default=1)


class SentMessage(Base):
    __tablename__ = 'sent_message'

    id: Mapped[int] = mapped_integer(primary_key=True, index=True)
    guild_id: Mapped[int] = mapped_integer(ForeignKey('guild.id'))
    channel_id: Mapped[Optional[int]]


class Guild(Base):
    __tablename__ = 'guild'

    id: Mapped[int] = mapped_integer(primary_key=True, index=True)

    initialized_channels: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={}
    )


class SessionFabric:

    def init_tables(self):
        if self.is_async:
            async def init_models(_engine):
                async with _engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

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
    def _build(db_uri: str,
               connect_args: dict | None = None,
               is_async: bool = True) -> tuple[AsyncEngine, async_sessionmaker]:
        if connect_args is None:
            connect_args = {}

        if is_async:
            engine = create_async_engine(
                db_uri,
                echo=False,
                pool_pre_ping=True,
                connect_args=connect_args
            )
            session_maker = async_sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
        else:
            engine = create_engine(
                db_uri,
                echo=False,
                pool_pre_ping=True,
                connect_args=connect_args
            )
            session_maker = sessionmaker(engine, expire_on_commit=False)

        return engine, session_maker

    @classmethod
    def build(cls,
              db_uri: str,
              connect_args: Optional[dict] = None,
              is_async: bool = True) -> Callable:
        engine, session_maker = cls._build(
            db_uri=db_uri,
            connect_args=connect_args,
            is_async=is_async,
        )
        self = cls(
            engine=engine,
            session_maker=session_maker,
            is_async=is_async,
        )

        return self.get_async if self.is_async else self.get_sync

    async def get_async(self) -> Generator:
        with suppress(IllegalStateChangeError):
            async with self.session_maker() as session:
                yield session

    def get_sync(self) -> Generator:
        with self.session_maker() as session:
            yield session
