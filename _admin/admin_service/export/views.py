# -*- coding: utf-8 -*-
import uuid

from flask import (Blueprint, render_template, g, request, url_for,
    current_app, send_from_directory, json, redirect, make_response, abort)

from flask.ext.login import login_required
from admin_service.export.ics import generate_ics
from admin_service.export.models import ExportICSConfig

from ..extensions import pages, csrf, db
from ..tasks import do_some_stuff
import trafaret as t

export = Blueprint('export', __name__, url_prefix='/export/', template_folder="templates")


@export.route('index')
@login_required
def index():
    return render_template('export/index.html')


@export.route('ics')
@login_required
def export_ics():
    if not g.user.team.exportics_config or \
            not g.user.team.exportics_config.calendar_prodid or \
            not g.user.team.exportics_config.config_slug:
        return redirect(url_for('export.setup_ics'))
    return render_template('export/ics.html',
                           config=g.user.team.exportics_config)


SETUP_FORM = t.Dict({
                     'calendar_prodid': t.String,
                     'query': t.String(allow_blank=True)
                    }).ignore_extra('_csrf_token')


@export.route('ics/setup', methods=['POST', 'GET'])
@login_required
def setup_ics():
    g.errors = []
    if request.method == 'POST':
        do_setup()
        if not g.errors:
            return redirect(url_for('export.export_ics'))
    return render_template('export/setup_ics.html',
                           errors=g.errors,
                           initial=g.user.team.exportics_config)


def do_setup():
    try:
        data = SETUP_FORM.check(request.form.to_dict())
    except t.DataError as e:
        g.errors += ['{}: {}'.format(key, value)
                     for key, value in e.error.items()]
        return

    sess = db.session()
    if not g.user.team.exportics_config:
        config = ExportICSConfig(team_id=g.user.team.id,
                                 config_slug=uuid.uuid4().hex)
        sess.add(config)
        sess.commit()
    else:
        config = g.user.team.exportics_config
    if not g.user.team.exportics_config.config_slug:
        data['config_slug'] = uuid.uuid4().hex
    sess.query(ExportICSConfig).filter(ExportICSConfig.id == config.id).update(data)
    sess.commit()


@export.route('ics/<slug>/calendar.ics')
def ics_feed(slug):
    sess = db.session()
    config = sess.query(ExportICSConfig).filter(ExportICSConfig.config_slug == slug).first()
    events_token = config.team.events_token
    events = current_app.events_api.get_events(
        events_token,
        offset=0,
        count=100,
        sorting='-when_start',
        query=config.query)
    calendar = generate_ics(events['events'], config)
    r = make_response(calendar)
    r.headers['Content-Type'] = 'text/calendar; charset=utf-8'
    r.headers['Content-Disposition'] = 'attachment;filename=' + slug[:8] + '.ics'
    return r
