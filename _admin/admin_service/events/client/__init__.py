import requests


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
        print(response)
        return response.json()
