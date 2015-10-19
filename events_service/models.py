import asyncio
from aiopg.sa import AsyncMetaData
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

from aiopg.sa import create_engine
from events_service.settings import DATABASE_HOST, DATABASE_PASSWORD,\
    DATABASE_NAME, DATABASE_USERNAME


metadata = AsyncMetaData()
Base = declarative_base(metadata=metadata)


LEVEL_OF_EVENT = ('NONE', 'TRAINEE', 'JUNIOR', 'MIDDLE', 'SENIOR')


class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    title = Column(String(256), nullable=False)
    agenda = Column(Text(), nullable=False)
    social = Column(Text(), doc='How to get to the event, useful links and comments.')
    image_url = Column(String(500))
    level = Column(Enum(*LEVEL_OF_EVENT, name='level_types'),
                   default='NONE', nullable=False)
    place = Column(String(256))
    when_start = Column(DateTime(), nullable=False)
    when_end = Column(DateTime())
    only_date = Column(Boolean(), default=True, nullable=False)
    registration_url = Column(String(500))
    special = Column(Boolean(), default=False,
                     doc='This event should be rendered in special way',
                     nullable=False)


@asyncio.coroutine
def setup(app):
    engine = yield from create_engine(user=DATABASE_USERNAME,
                                      database=DATABASE_NAME,
                                      host=DATABASE_HOST,
                                      password=DATABASE_PASSWORD)
    app['db_engine'] = engine
    app['db_declarative_base'] = Base
    metadata.bind = engine
