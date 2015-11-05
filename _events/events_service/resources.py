import ast
import asyncio
import operator
import uuid
from aiohttp.web_exceptions import HTTPBadRequest
from events_service.permissions import KeyProvided
from rest_utils.resource import ModelResource, ModelBaseResource, CreateModelMixin
from events_service.models import Event, EventsProvider
from rest_utils.validator import ModelValidator


class EventValidator(ModelValidator):
    def __init__(self):
        super().__init__(Event)

    def cut_provider(self, trafaret, column):
        pass


def parse_query(model, query):
    operators = {
        ast.And: operator.and_,
        ast.Or: operator.or_,
        ast.Eq: operator.eq,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
    }

    def get_operator(op, left, right):
        return operators[op](left, right)

    def _eval(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.NameConstant):
            return node.value
        elif isinstance(node, ast.Name):
            return model.__mapper__.columns[node.id]
        elif isinstance(node, ast.Compare):
            if len(node.comparators) != 1 and len(node.ops) != 1:
                raise TypeError(node)
            return get_operator(type(node.ops[0]),
                                _eval(node.left), _eval(node.comparators[0]))
        elif isinstance(node, ast.BoolOp):
            return get_operator(type(node.op),
                                _eval(node.values[0]), _eval(node.values[1]))
        raise TypeError(node)

    return _eval(ast.parse(query, mode='eval').body)


class EventResource(ModelResource):
    model = Event
    permissions = [KeyProvided()]
    validator = EventValidator()

    def base_query(self, request):
        base_query = super().base_query(request).\
            where(Event.provider == request.events_provider.id)

        query = request.GET.get('query')
        if query:
            try:
                filter = parse_query(Event, query)
            except (TypeError, SyntaxError) as e:
                raise HTTPBadRequest(text=str(e))
            base_query = base_query.where(filter)
        return base_query

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

    def cut_key(self, trafaret, column):
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
