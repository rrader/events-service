# -*- coding: utf-8 -*-
from collections import OrderedDict
import uuid
import dateutil.parser
from github import Github
from admin_service.digestmonkey import mailchimp_utils
from admin_service.digestmonkey.github_utils import get_github_repo, format_template
from admin_service.digestmonkey.mailchimp_utils import get_mailchimp_api
from admin_service.digestmonkey.models import DigestMonkeyConfig, PublishedDigest

from flask import (Blueprint, render_template, g, request, url_for,
    current_app, send_from_directory, json, redirect, make_response, abort)

from flask.ext.login import login_required
from admin_service.events.client import EventsServiceAPIError
from admin_service.events.views import EventsList

from ..extensions import pages, csrf, cache, db
import trafaret as t

digestmonkey = Blueprint('digestmonkey', __name__, url_prefix='/digestmonkey/', template_folder="templates")


@digestmonkey.route('index')
@login_required
def index():
    if not g.user.team.digestmonkey_config or \
            not g.user.team.digestmonkey_config.mailchimp_key or \
            not g.user.team.digestmonkey_config.templates_uri or \
            not g.user.team.digestmonkey_config.github_key:
        return redirect(url_for('digestmonkey.setup'))
    sess = db.session()
    r = sess.query(PublishedDigest).order_by(PublishedDigest.id.desc()).limit(5).all()
    return render_template('digestmonkey/index.html', last_campaigns=r)


SETUP_FORM = t.Dict({
                     'mailchimp_key': t.String,
                     'templates_uri': t.String(allow_blank=True),
                     'github_key': t.String(allow_blank=True),
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


def get_event(id_):
    return current_app.events_api.get_event(g.user.team.events_token, id_)


class EventsSubset(EventsList):
    template = 'digestmonkey/subset.html'

    def post(self):
        if request.form['submit'] == 'subset':
            events_list = [get_event(k) for k, v in request.form.to_dict().items() if v == 'on']
            if not events_list:
                return redirect(request.url)
            subset_id = uuid.uuid4().hex
            cache.set(subset_id, {'list': events_list}, timeout=60*60*24)
            return redirect(url_for('digestmonkey.choose_template', subset_id=subset_id))
        return redirect(request.url)

digestmonkey.add_url_rule('subset', view_func=login_required(EventsSubset.as_view('make_subset')))


@digestmonkey.route('choose-template/<subset_id>')
@login_required
def choose_template(subset_id):
    templates = [file for file in get_github_repo().get_dir_contents('/')
                 if file.name.endswith(".html") or file.name.endswith(".template")]
    return render_template('digestmonkey/choose_template.html',
                           templates=templates,
                           subset_id=subset_id,
                           subset=cache.get(subset_id))


@digestmonkey.route('choose-template/<subset_id>/<filename>')
@login_required
def template_chosen(subset_id, filename):
    data = cache.get(subset_id)
    data['template'] = filename
    cache.set(subset_id, data, timeout=60*60*24)
    return redirect(url_for('digestmonkey.configure_template', subset_id=subset_id))


@digestmonkey.route('configure-template/<subset_id>', methods=['POST', 'GET'])
@login_required
def configure_template(subset_id):
    data = cache.get(subset_id)
    if request.method == 'POST':
        variables = request.form.to_dict()
        if '_csrf_token' in variables:
            del variables['_csrf_token']
        data['variables'] = variables
        cache.set(subset_id, data, timeout=60*60*24)
        return redirect(url_for('digestmonkey.preview', subset_id=subset_id))
    variables = json.loads(
        get_github_repo().get_file_contents("/{}.defaults".format(data['template'])). \
            decoded_content.decode()
    )
    variables.update(data.get('variables', {}))
    return render_template('digestmonkey/configure_template.html',
                           subset_id=subset_id,
                           subset=cache.get(subset_id),
                           variables=OrderedDict(sorted(variables.items())))


@digestmonkey.route('preview/<subset_id>')
@login_required
def preview(subset_id):
    data = cache.get(subset_id)
    variables = data['variables'].copy()
    variables.update({'events': sorted_eventslist(
                        data['list']
                      ),
                      'special_events': sorted_eventslist(
                          [e for e in data['list'] if e['special']]
                      )})
    preview = format_template(data['template'], variables)
    data['preview'] = preview
    cache.set(subset_id, data, timeout=60*60*24)
    return render_template('digestmonkey/preview.html',
                           subset_id=subset_id,
                           subset=cache.get(subset_id))


@digestmonkey.route('preview-content/<subset_id>')
@login_required
def preview_content(subset_id):
    data = cache.get(subset_id)
    return data['preview']


MAILLIST_SETUP_FORM = t.Dict({
                        'subject': t.String,
                        'from_name': t.String,
                        'from_email': t.String,
                        }).ignore_extra('_csrf_token')


@digestmonkey.route('choose-maillist/<subset_id>', methods=['POST', 'GET'])
@login_required
def choose_maillist(subset_id):
    data = cache.get(subset_id)
    g.errors = []
    if request.method == 'POST':
        url = do_create_campaign(data)
        if not g.errors:
            return redirect(url)

    s_list = request.args.get('s_list')
    initial = {}
    initial.update(request.form.to_dict())

    if s_list:
        list_info = mailchimp_utils.get_list(s_list)

        subject = list_info['default_subject']
        if subject:
            initial['subject'] = subject

        from_name = list_info['default_from_name']
        if from_name:
            initial['from_name'] = from_name

        from_email = list_info['default_from_email']
        if from_email:
            initial['from_email'] = from_email

        data['s_list'] = s_list
        data['s_list_name'] = list_info['name']

    cache.set(subset_id, data, timeout=60*60*24)
    return render_template('digestmonkey/choose_maillist.html',
                           subset_id=subset_id,
                           subset=cache.get(subset_id),
                           lists=mailchimp_utils.list_list(),
                           s_list=s_list,
                           initial=initial,
                           errors=g.errors)


def do_create_campaign(data):
    try:
        data.update(MAILLIST_SETUP_FORM.check(request.form.to_dict()))
    except t.DataError as e:
        g.errors += ['{}: {}'.format(key, value)
                     for key, value in e.error.items()]
        return
    options = {
        'list_id': data['s_list'],
        'subject': data['subject'],
        'from_name': data['from_name'],
        'from_email': data['from_email'],
        }

    content = {
        'html': data['preview'],
    }

    r = get_mailchimp_api().campaigns.create('regular', options, content)
    url = "https://admin.mailchimp.com/campaigns/wizard/html-paste?id={}". \
        format(r['web_id'])

    d = PublishedDigest(events_data=data['list'],
                        events_ids=[int(e['id']) for e in data['list']],
                        template=data['template'],
                        preview=data['preview'],
                        s_list=data['s_list'],
                        s_list_name=data['s_list_name'],
                        from_name=data['from_name'],
                        from_email=data['from_email'],
                        subject=data['subject'],
                        campaign_id=r['id'],
                        web_id=r['web_id'],
                        team_id=g.user.team.id)
    sess = db.session()
    sess.add(d)
    sess.commit()

    return url


def sorted_eventslist(elist):
    return sorted(elist, key=lambda e: dateutil.parser.parse(e['when_start']))


@digestmonkey.route('digest-details/<id_>')
@login_required
def digest_details(id_):
    sess = db.session()
    digest = sess.query(PublishedDigest).filter(PublishedDigest.id == int(id_)).first()
    return render_template('digestmonkey/digest_details.html',
                           digest=digest)


@digestmonkey.route('digest-details/<id_>/preview')
@login_required
def digest_details_preview(id_):
    sess = db.session()
    digest = sess.query(PublishedDigest).filter(PublishedDigest.id == int(id_)).first()
    return digest.preview
