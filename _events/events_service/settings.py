import os
from urllib.parse import urlparse


default_db = 'postgres://user:pass@127.0.0.1:5432/dbname'
DATABASE_URL = os.environ.get('DATABASE_URL', default_db)
url = urlparse(DATABASE_URL)

DATABASE_HOST = '{}:{}'.format(url.hostname, url.port)
DATABASE_NAME = url.path[1:]
DATABASE_USERNAME = url.username
DATABASE_PASSWORD = url.password
