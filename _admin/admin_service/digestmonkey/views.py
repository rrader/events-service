# -*- coding: utf-8 -*-
from admin_service.digestmonkey.models import DigestMonkeyConfig

from flask import (Blueprint, render_template, g, request, url_for,
    current_app, send_from_directory, json, redirect, make_response, abort)

from flask.ext.login import login_required
from admin_service.events.client import EventsServiceAPIError

from ..extensions import pages, csrf, cache, db
import trafaret as t

digestmonkey = Blueprint('digestmonkey', __name__, url_prefix='/digestmonkey/', template_folder="templates")


@digestmonkey.route('index')
@login_required
def index():
    if not g.user.team.digestmonkey_config or \
            not g.user.team.digestmonkey_config.mailchimp_key:
        return redirect(url_for('digestmonkey.setup'))
    return render_template('digestmonkey/index.html')



SETUP_FORM = t.Dict({
                     'mailchimp_key': t.String,
                    }).ignore_extra('_csrf_token')


@digestmonkey.route('setup', methods=['POST', 'GET'])
@login_required
def setup():
    g.errors = []
    if request.method == 'POST':
        do_setup()
        if not g.errors:
            return redirect(url_for('digestmonkey.index'))
    return render_template('digestmonkey/setup.html',
                           errors=g.errors,
                           initial=g.user.team.digestmonkey_config)


def do_setup():
    try:
        data = SETUP_FORM.check(request.form.to_dict())
    except t.DataError as e:
        g.errors += ['{}: {}'.format(key, value)
                     for key, value in e.error.items()]
        return

    sess = db.session()
    if not g.user.team.digestmonkey_config:
        config = DigestMonkeyConfig(team_id=g.user.team.id)
        sess.add(config)
        sess.commit()
    else:
        config = g.user.team.digestmonkey_config
    sess.query(DigestMonkeyConfig).filter(DigestMonkeyConfig.id == config.id).update(data)
    sess.commit()
