#pylint:disable-msg=W0612
import datetime

import os
import dateutil
from flask import Flask, request, render_template, g
from flask.ext import login
from celery import Celery
from admin_service.events.client import EventsServiceAPI

from .extensions import (db, mail, pages, manager, login_manager, babel,
    migrate, csrf, celery, cache)

# blueprints
from .frontend import frontend
from .auth import auth
from .api import api, initialize_api
from .events import events
from .digestmonkey import digestmonkey
from .export import export

__all__ = ('create_app', 'create_celery', )

BLUEPRINTS = (
    frontend,
    auth,
    api,
    events,
    digestmonkey,
    export
)


def create_app(config=None, app_name='admin_service', blueprints=None):
    app = Flask(app_name,
        static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'),
        template_folder="templates"
    )

    app.config.from_object('admin_service.config')
    # app.config.from_pyfile('../local.cfg', silent=True)
    if config:
        app.config.from_pyfile(config)

    if blueprints is None:
        blueprints = BLUEPRINTS

    blueprints_fabrics(app, blueprints)
    extensions_fabrics(app)
    api_fabrics(app)  # this must be called after extensions_fabrics
    configure_logging(app)
    template_filters(app)

    error_pages(app)
    gvars(app)

    return app


def create_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


def blueprints_fabrics(app, blueprints):
    """Configure blueprints in views."""

    for blueprint in blueprints:
        app.register_blueprint(blueprint)


def extensions_fabrics(app):
    db.init_app(app)
    mail.init_app(app)
    babel.init_app(app)
    pages.init_app(app)
    login_manager.init_app(app)
    manager.init_app(app, flask_sqlalchemy_db=db)
    migrate.init_app(app, db)
    csrf.init_app(app)
    celery.config_from_object(app.config)
    cache.init_app(app)


def api_fabrics(app):
    initialize_api(app)


def error_pages(app):
    # HTTP error pages definitions

    @app.errorhandler(403)
    def forbidden_page(error):
        return render_template("misc/403.html"), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("misc/404.html"), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return render_template("misc/405.html"), 404

    @app.errorhandler(500)
    def server_error_page(error):
        return render_template("misc/500.html"), 500


def gvars(app):
    @app.before_first_request
    def events_api():
        app.events_api = EventsServiceAPI(app.config['EVENTS_SERVICE_URL'])

    @app.before_request
    def gdebug():
        if app.debug:
            g.debug = True
        else:
            g.debug = False

    from .models import User

    @login_manager.user_loader
    def load_user(userid):
        try:
            return User.query.get(int(userid))
        except (TypeError, ValueError):
            pass

    @app.before_request
    def guser():
        g.user = login.current_user

    @app.context_processor
    def inject_user():
        try:
            return {'user': g.user}
        except AttributeError:
            return {'user': None}

    @app.context_processor
    def dateutils():
        today = datetime.date.today()
        cw_monday = today + datetime.timedelta(days=-today.weekday())
        cw_sunday = today + datetime.timedelta(days=7 - today.weekday())
        nw_monday = today + datetime.timedelta(days=-today.weekday() + 7)
        nw_sunday = today + datetime.timedelta(days=7 - today.weekday() + 7)
        return dict(cw_monday=cw_monday,
                    cw_sunday=cw_sunday,
                    nw_monday=nw_monday,
                    nw_sunday=nw_sunday)

    @babel.localeselector
    def get_locale():
        if g.user:
            if hasattr(g.user, 'ui_lang'):
                return g.user.ui_lang

        accept_languages = app.config.get('ACCEPT_LANGUAGES')
        return request.accept_languages.best_match(accept_languages)


def configure_logging(app):
    """Configure file(info) and email(error) logging."""

    if app.debug or app.testing:
        # Skip debug and test mode. Just check standard output.
        return

    import logging
    from logging.handlers import SMTPHandler

    # Set info level on logger, which might be overwritten by handers.
    # Suppress DEBUG messages.
    app.logger.setLevel(logging.INFO)

    info_log = os.path.join(app.config['LOG_FOLDER'], 'info.log')
    info_file_handler = logging.handlers.RotatingFileHandler(info_log, maxBytes=100000, backupCount=10)
    info_file_handler.setLevel(logging.INFO)
    info_file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')
    )
    app.logger.addHandler(info_file_handler)

    # Testing
    #app.logger.info("testing info.")
    #app.logger.warn("testing warn.")
    #app.logger.error("testing error.")

    mail_handler = SMTPHandler(app.config['MAIL_SERVER'],
                               app.config['MAIL_USERNAME'],
                               app.config['ADMINS'],
                               'O_ops... %s failed!' % app.config['PROJECT'],
                               (app.config['MAIL_USERNAME'],
                                app.config['MAIL_PASSWORD']))
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')
    )
    app.logger.addHandler(mail_handler)


def template_filters(app):
    @app.template_filter('strfdatetime')
    def _jinja2_filter_datetime(date, fmt=None):
        date = dateutil.parser.parse(date)
        native = date.replace(tzinfo=None)
        return native.strftime('%Y-%m-%d %H:%M')

    @app.template_filter('strfdate')
    def _jinja2_filter_date(date, fmt=None):
        date = dateutil.parser.parse(date)
        native = date.replace(tzinfo=None)
        return native.strftime('%Y-%m-%d')

    @app.template_filter('strftime')
    def _jinja2_filter_date(date, fmt):
        return date.strftime(fmt)
