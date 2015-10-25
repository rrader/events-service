import asyncio
from aiopg.sa import AsyncMetaData
from sqlalchemy import Column, Integer, String, Unicode, UnicodeText, Enum, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

from aiopg.sa import create_engine
from events_service.settings import DATABASE_URL
from sqlalchemy.orm import relationship

metadata = AsyncMetaData()
Base = declarative_base(metadata=metadata)


LEVEL_OF_EVENT = ('NONE', 'TRAINEE', 'JUNIOR', 'MIDDLE', 'SENIOR')


class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    title = Column(Unicode(256), nullable=False)
    agenda = Column(UnicodeText(), nullable=False)
    social = Column(UnicodeText(), doc='How to get to the event, useful links and comments.')
    image_url = Column(String(500), nullable=True)
    level = Column(Enum(*LEVEL_OF_EVENT, name='level_types'),
                   default='NONE', nullable=False)
    place = Column(Unicode(256))
    when_start = Column(DateTime(), nullable=False)
    when_end = Column(DateTime())
    only_date = Column(Boolean(), default=True, nullable=False)
    registration_url = Column(String(500))
    special = Column(Boolean(), default=False,
                     doc='This event should be rendered in special way',
                     nullable=False)
    provider = Column(Integer, ForeignKey('provider.id'), nullable=False)
    metainfo = Column(UnicodeText(), nullable=False, server_default='{}',
                      doc='JSON field contains some additional information')


class EventsProvider(Base):
    __tablename__ = 'provider'

    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    key = Column(String(256), nullable=False)
    events = relationship('Event')


@asyncio.coroutine
def setup(app):
    engine = yield from create_engine(DATABASE_URL)
    app['db_engine'] = engine
    app['db_declarative_base'] = Base
    metadata.bind = engine
