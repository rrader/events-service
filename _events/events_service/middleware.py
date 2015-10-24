import asyncio
from events_service.models import EventsProvider


@asyncio.coroutine
def middleware_factory(app, handler):
    @asyncio.coroutine
    def middleware(request):
        key = request.headers.get('CLIENT-KEY')
        provider = None
        if key:
            with (yield from app['db_engine']) as conn:
                result = yield from conn.execute(
                    EventsProvider.__table__.select().where(EventsProvider.key == key))
                provider = yield from result.fetchone()
        request.events_provider = provider
        result = yield from handler(request)
        return result
    return middleware
