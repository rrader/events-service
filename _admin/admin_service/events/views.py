# -*- coding: utf-8 -*-
import dateutil

from flask import (Blueprint, render_template, g, request, url_for,
    current_app, send_from_directory, json, redirect, make_response, abort)

from flask.ext.login import login_required

from ..extensions import pages, csrf

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


@events.route('event/create', methods=['GET', 'POST'])
@login_required
def create_event():
    g.errors = []
    if request.method == 'POST':
        user = do_create_event()
        if not g.errors:
            return redirect(url_for('auth.team', id_=user.team_id))
    return render_template('auth/user_create.html', errors=g.errors)


def do_create_event():
    pass
