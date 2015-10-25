# -*- coding: utf-8 -*-
import dateutil

from flask import (Blueprint, render_template, g, request, url_for,
    current_app, send_from_directory, json, redirect, make_response, abort)

from flask.ext.login import login_required

from ..extensions import pages, csrf
import trafaret as t

events = Blueprint('events', __name__, url_prefix='/events/', template_folder="templates")


@events.route('list')
@login_required
def events_list():
    offset = int(request.args.get('offset', 0))
    count = int(request.args.get('count', 10))
    page = int(offset/count) + 1
    r = current_app.events_api.get_events(g.user.team.events_token,
                                          offset=offset,
                                          count=count)
    return render_template('events/events.html',
                           events_data=r,
                           offset=offset,
                           count=count,
                           page=page)


EVENT_CREATION_FORM = t.Dict({
                             'title': t.String,
                             'agenda': t.String,
                             'social': t.String(allow_blank=True),
                             'place': t.String(allow_blank=True),
                             'registration_url': t.URL(allow_blank=True),
                             'image_url': t.URL(allow_blank=True),
                             'level': t.Enum('NONE', 'TRAINEE', 'JUNIOR', 'MIDDLE', 'SENIOR'),
                             t.Key('special', default=False): t.StrBool,
                             'when_start': t.String,
                             'when_end': t.String(allow_blank=True),
                             t.Key('include_time', default=False): t.StrBool,
                            }).ignore_extra('_csrf_token')


@events.route('event/create', methods=['GET', 'POST'])
@login_required
def create_event():
    g.errors = []
    if request.method == 'POST':
        do_create_event()
        if not g.errors:
            return redirect(url_for('events.events_list'))
    return render_template('events/event_create.html', errors=g.errors)


def do_create_event():
    try:
        data = EVENT_CREATION_FORM.check(request.form.to_dict())
    except t.DataError as e:
        g.errors += ['{}: {}'.format(key, value)
                     for key, value in e.error.items()]
        return
    print(data)
    current_app.events_api.add_event(data)
