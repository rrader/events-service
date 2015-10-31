import asyncio
import aiohttp
import json
from aio_manager import Manager, Command
from events_service.models import Event, EventsProvider
from dateutil.parser import parse


class ImportEvents(Command):
    """
    Import events from IT KPI Site
    """
    def __init__(self, app):
        super().__init__('import', app)

    def run(self, app, args):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.load(app, args))

    @asyncio.coroutine
    def load(self, app, args):
        with (yield from app['db_engine']) as conn:
            r = yield from conn.execute(EventsProvider.__table__.select().
                                        where(EventsProvider.key == args.provider_key))
            provider = yield from r.fetchone()
        print("Provider " + provider.name)

        result = yield from aiohttp.get('http://it.kpi.pp.ua/events/events.json?start=0&end=4200000000')
        d = yield from result.json()

        with (yield from app['db_engine']) as conn:
            count = len(d['events'])
            for i, imp_event in enumerate(d['events']):
                event = self.convert(imp_event, provider.id)
                yield from conn.execute(Event.__table__.insert().values(**event))
                print('{}/{} imported...'.format(i + 1, count))

    def convert(self, imp_event, provider):
        event = imp_event.copy()
        event.pop('id')
        event['only_date'] = not event.pop('when_time_required')
        event['registration_url'] = event.pop('registration')  # empty
        start_time = event.pop('start_time')
        end_time = event.pop('end_time')
        start = event.pop('start')
        end = event.pop('end')
        event['provider'] = provider
        event['metainfo'] = json.dumps({'creator': event.pop('owner')})
        if not event['only_date']:
            event['when_start'] = parse('{} {}'.format(start, start_time))
            if end:
                if end_time:
                    event['when_end'] = parse('{} {}'.format(end, end_time))
                else:
                    event['when_end'] = parse(end)
            else:
                event['when_end'] = None
        else:
            event['when_start'] = parse(start)
            if end:
                event['when_end'] = parse(end)
            else:
                event['when_end'] = None
        return event

    def configure_parser(self, parser):
        super().configure_parser(parser)
        parser.add_argument('provider_key', metavar='KEY',
                            help='key of provider')
        # parser.add_argument('--key', metavar='KEY',
        #                     help='key (random will be generated if not provided)')


if __name__ == '__main__':
    pass
