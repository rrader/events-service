import uuid
import flask_restless.manager
from flask import (Blueprint, render_template, current_app, abort)
from sqlalchemy.orm.exc import NoResultFound
from admin_service.auth.models import Team
from admin_service.events.models import SuggestedEvent

import trafaret as t

from ..extensions import manager, csrf


def pre_get_many(**kw):
    abort(405)


def get_team_by_name(name):
    try:
        return Team.query.filter(Team.name == name).one().id
    except NoResultFound:
        raise t.DataError('Team not found')


EVENT_SUGGESTION_TRAFARET = t.Dict({
                             'title': t.String,
                             'agenda': t.String,
                             'social': t.String(allow_blank=True),
                             'place': t.String(allow_blank=True),
                             'registration_url': t.URL(allow_blank=True) | t.Null,
                             'image_url': t.URL(allow_blank=True) | t.String(max_length=0, allow_blank=True),
                             'level': t.Enum('NONE', 'TRAINEE', 'JUNIOR', 'MIDDLE', 'SENIOR'),
                             'when_start': t.String,
                             'when_end': (t.String(allow_blank=True) >>
                                          (lambda x: None if not x else x)) | t.Null,
                             'only_date': t.StrBool(),
                             'team': t.String() >> get_team_by_name,
                             'submitter_email': t.Email()
                            })


def suggested_event_deserializer(data):
    try:
        validated = EVENT_SUGGESTION_TRAFARET.check(data)
    except t.DataError as e:
        return abort(400, e.error)
    validated['secret'] = uuid.uuid4().hex
    return SuggestedEvent(**validated)
    # return person_schema.load(data).data


def initialize_api(app):
    # List all Flask-Restless APIs here
    with app.app_context():
        manager.create_api(SuggestedEvent, methods=['GET', 'POST'],
                           app=app,
                           url_prefix='/api/v1',
                           preprocessors={
                               # 'GET_SINGLE': [pre_get_single],
                               'GET_MANY': [pre_get_many],
                               # 'DELETE': [pre_delete]
                               },
                           deserializer=suggested_event_deserializer)

    # Disable CSRF check for REST API
    # FIXME: I know :(
    api_blueprints = [v for x, v in app.blueprints.items()
                      if v.import_name == flask_restless.manager.__name__]
    for blueprint in api_blueprints:
        csrf.exempt(blueprint)


api = Blueprint('api', __name__)
