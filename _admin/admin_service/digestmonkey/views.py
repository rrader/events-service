# -*- coding: utf-8 -*-
from collections import OrderedDict, defaultdict

import dateutil.parser
from flask import (Blueprint, render_template, g, request, url_for,
                   redirect)
import trafaret as t

from admin_service.digestmonkey import mailchimp_utils
from admin_service.digestmonkey.github_utils import get_github_repo
from admin_service.digestmonkey.mailchimp_utils import get_mailchimp_api
from admin_service.digestmonkey.models import DigestMonkeyConfig, PublishedDigest
from flask.ext.login import login_required
from admin_service.digestmonkey.utils.digest import init_digest, set_variable, set_default_template_variables, \
    generate_preview
from admin_service.digestmonkey.utils.query_parser import parse_named_values
from admin_service.events.views import EventsList
from ..extensions import cache, db

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


class EventsSubset(EventsList):

    template = 'digestmonkey/subset.html'
    def post(self):
        if request.form['submit'] == 'subset':
            events_list = [k for k, v in request.form.to_dict().items() if v == 'on']
            if not events_list:
                return redirect(request.url)
            params = parse_named_values(request.form['query'])
            subset_id = init_digest(events_list, params)
            return redirect(url_for('digestmonkey.choose_template', subset_id=subset_id))
        return redirect(request.url)


digestmonkey.add_url_rule('subset', view_func=login_required(EventsSubset.as_view('make_subset')))


@digestmonkey.route('choose-template/<subset_id>')
@login_required
def choose_template(subset_id):
    templates = [file for file in get_github_repo().get_dir_contents('/')
                 if file.name.endswith(".html") or file.name.endswith(".template")]
    if len(templates) == 1:
        set_variable(subset_id, 'template', templates[0].name)
        return redirect(url_for('digestmonkey.configure_template', subset_id=subset_id))
    else:
        return render_template('digestmonkey/choose_template.html',
                               templates=templates,
                               subset_id=subset_id,
                               subset=cache.get(subset_id))


@digestmonkey.route('choose-template/<subset_id>/<filename>')
@login_required
def template_chosen(subset_id, filename):
    set_variable(subset_id, 'template', filename)
    return redirect(url_for('digestmonkey.configure_template', subset_id=subset_id))


@digestmonkey.route('configure-template/<subset_id>', methods=['POST', 'GET'])
@login_required
def configure_template(subset_id):
    if request.method == 'POST':
        data = cache.get(subset_id)
        variables = request.form.to_dict()
        if '_csrf_token' in variables:
            del variables['_csrf_token']
        data['variables'] = variables
        cache.set(subset_id, data, timeout=60*60*24)
        return redirect(url_for('digestmonkey.preview', subset_id=subset_id))
    variables = set_default_template_variables(subset_id)
    return render_template('digestmonkey/configure_template.html',
                           subset_id=subset_id,
                           subset=cache.get(subset_id),
                           variables=OrderedDict(sorted(variables.items())))


@digestmonkey.route('preview/<subset_id>')
@login_required
def preview(subset_id):
    generate_preview(subset_id)
    return redirect(url_for('digestmonkey.choose_maillist', subset_id=subset_id))


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
    params = defaultdict(str, data['query_params'])

    if s_list:
        list_info = mailchimp_utils.get_list(s_list)

        subject = list_info['default_subject']
        if subject:
            initial['subject'] = subject.format(**params)

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
