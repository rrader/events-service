import asyncio
import json
import uuid
from events_service.permissions import KeyProvided
from rest_utils.resource import ModelResource, ModelBaseResource, CreateModelMixin
from events_service.models import Event, EventsProvider
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


class EventProviderValidator(ModelValidator):
    def __init__(self):
        super().__init__(EventsProvider)

    def cut_key(self, column):
        pass


class EventsProviderResource(CreateModelMixin,
                             ModelBaseResource):
    model = EventsProvider
    validator = EventProviderValidator()

    def get_path(self):
        return r'/providers'

    @asyncio.coroutine
    def perform_create(self, request, data):
        data['key'] = uuid.uuid4().hex
        id_ = yield from super().perform_create(request, data)
        return id_


@asyncio.coroutine
def setup(app):
    EventResource(app).register()
    EventsProviderResource(app).register()
