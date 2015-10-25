import json
import requests


class EventsServiceAPIError(Exception):
    def __init__(self, errors=None):
        if not errors:
            errors = []
        super().__init__()
        self.errors = errors

    def __str__(self):
        return '; '.join(self.errors)


class EventsServiceAPI:
    def __init__(self, url):
        self.url = url
        self.session = requests.Session()

    def register_provider(self, name):
        response = self.session.post('{}/providers'.format(self.url),
                                     json={'name': name})
        return response.json()['key']

    def get_events(self, api_key, offset=0, count=10):
        response = self.session.get('{}/events?count={}&offset={}'.
                                    format(self.url, count, offset),
                                    headers={'Client-Key': api_key})
        self.process_errors(response)
        return response.json()

    def get_event(self, api_key, id_):
        response = self.session.get('{}/events/{}'.
                                    format(self.url, id_),
                                    headers={'Client-Key': api_key})
        self.process_errors(response)
        data = response.json()
        data['metainfo'] = json.loads(data.pop('metainfo'))
        return data

    def add_event(self, api_key, metainfo, **kwargs):
        data = kwargs.copy()
        data.update({'metainfo': json.dumps(metainfo)})
        response = self.session.post('{}/events'.
                                     format(self.url),
                                     json=data,
                                     headers={'Client-Key': api_key})
        self.process_errors(response)
        return response.headers['location']

    def process_errors(self, response):
        if response.status_code > 299:
            if response.status_code == 400:
                raise EventsServiceAPIError(['{}: {} [api]'.format(k, v) for k, v in response.json().items()])
            raise EventsServiceAPIError(['Events Service returned error'])
