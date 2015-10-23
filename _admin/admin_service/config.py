# -*- coding: utf-8 -*-

DEBUG = True
SECRET_KEY = 'change me please'

from os.path import dirname, abspath, join
SQLALCHEMY_DATABASE_URI = 'sqlite:////%s/data.sqlite' % dirname(abspath(__file__))
SQLALCHEMY_ECHO = True

# flatpages
FLATPAGES_EXTENSION = '.md'
FLATPAGES_ROOT = join(dirname(__file__), 'docs')
del dirname, abspath, join

# default babel values
BABEL_DEFAULT_LOCALE = 'en'
BABEL_DEFAULT_TIMEZONE = 'UTC'
ACCEPT_LANGUAGES = ['en', 'ru', ]

# available languages
LANGUAGES = {
    'en': u'English',
    'uk': u'Українська'
}

# make sure that you have started debug mail server using command
# $ make mail
MAIL_SERVER = 'localhost'
MAIL_PORT = 20025
MAIL_USE_SSL = False
MAIL_USERNAME = 'your@email.address'
#MAIL_PASSWORD = 'topsecret'

# Celery
BROKER_TRANSPORT = 'redis'
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_SERIALIZER = 'json'
CELERY_DISABLE_RATE_LIMITS = True
CELERY_ACCEPT_CONTENT = ['json',]

# cache
CACHE_TYPE = 'memcached'
CACHE_MEMCACHED_SERVERS = ['127.0.0.1:11211', ]
# CACHE_MEMCACHED_USERNAME =
# CACHE_MEMCACHED_PASSWORD =

# Auth
SESSION_COOKIE_NAME = 'session'

SOCIAL_AUTH_LOGIN_URL = '/'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/auth/loggedin'
SOCIAL_AUTH_USER_MODEL = 'admin_service.models.User'
SOCIAL_AUTH_AUTHENTICATION_BACKENDS = (
    'social.backends.github.GithubOAuth2',
)

# Documnetation http://psa.matiasaguirre.net/docs/backends/index.html
# https://github.com/settings/applications/
SOCIAL_AUTH_GITHUB_KEY = '8b643b3f60a3dd4470e7'
SOCIAL_AUTH_GITHUB_SECRET = '3e07a41b69244ec209db690e1babab3ca1d33291'
SOCIAL_AUTH_GITHUB_SCOPE = ['user:email']
