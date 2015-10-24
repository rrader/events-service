import asyncio
from events_service.permissions import KeyProvided
from rest_utils.resource import ModelResource
from events_service.models import Event
from rest_utils.validator import ModelValidator


class EventValidator(ModelValidator):
    def __init__(self):
        super().__init__(Event)

    def cut_provider(self, column):
        pass


class EventResource(ModelResource):
    model = Event
    permissions = [KeyProvided()]
    validator = EventValidator()

    def base_query(self, request):
        return super().base_query(request).\
            where(Event.provider == request.events_provider.id)

    def get_path(self):
        return r'/events'

    @asyncio.coroutine
    def perform_create(self, request, data):
        data['provider'] = request.events_provider.id
        id_ = yield from super().perform_create(request, data)
        return id_


@asyncio.coroutine
def setup(app):
    EventResource(app).register()
