# -*- coding: utf-8 -*-
#
from admin_service import create_app, create_celery

app = create_app()
celery = create_celery(app)
celery.start()
