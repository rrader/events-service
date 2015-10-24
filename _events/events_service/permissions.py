from rest_utils.permissions import Permission


class KeyProvided(Permission):
    def check(self, request):
        return request.events_provider is not None
