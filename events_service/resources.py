import asyncio
import trafaret as t
from rest_utils.resource import ModelResource
from events_service.models import Event


class EventResource(ModelResource):
    model = Event

    def get_path(self):
        return r'/events'


@asyncio.coroutine
def setup(app):
    EventResource(app).register()
