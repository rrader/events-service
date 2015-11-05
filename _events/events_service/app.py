import asyncio
from aiohttp.web import Application
from events_service import models, resources
from events_service.middleware import middleware_factory
import logging


def build_application():
    loop = asyncio.get_event_loop()
    app = Application(loop=loop, middlewares=[middleware_factory])
    loop.run_until_complete(models.setup(app))
    loop.run_until_complete(resources.setup(app))
    logging.info('Application created')
    return app


if __name__ == "__main__":
    pass
