import asyncio
import uuid
from aio_manager import Manager, Command
from aio_manager.commands.ext import sqlalchemy
from events_service import settings
from events_service.app import build_application
from events_service.models import Base, EventsProvider
from utils.itkpiloader import ImportEvents


class AddProvider(Command):
    """
    Add EventsProvider
    """
    def __init__(self, app):
        super().__init__('add_provider', app)

    def run(self, app, args):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.add_provider(app, args))

    @asyncio.coroutine
    def add_provider(self, app, args):
        with (yield from app['db_engine']) as conn:
            key = args.key
            if not key:
                key = uuid.uuid4().hex
            yield from conn.execute(EventsProvider.__table__.insert().
                                    values(name=args.name,
                                           key=key))
            print('{}: {}'.format(args.name, key))

    def configure_parser(self, parser):
        super().configure_parser(parser)
        parser.add_argument('name', metavar='NAME',
                            help='name of provider')
        parser.add_argument('--key', metavar='KEY',
                            help='key (random will be generated if not provided)')


app = build_application()
manager = Manager(app)

manager.add_command(AddProvider(app))
manager.add_command(ImportEvents(app))

sqlalchemy.configure_manager(manager, app, Base,  # TODO: use app['engine'] in manager
                             settings.DATABASE_USERNAME,
                             settings.DATABASE_NAME,
                             settings.DATABASE_HOST,
                             settings.DATABASE_PASSWORD)

if __name__ == "__main__":
    manager.run()
