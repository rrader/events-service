import uuid
import logging

from flask import (Blueprint, render_template, g, request, url_for,
    current_app, send_from_directory, json, redirect, make_response, abort)

from flask.ext.login import login_required
from flask.views import MethodView
from admin_service.events.client import EventsServiceAPIError
from admin_service.events.models import SuggestedEvent

from ..extensions import pages, csrf, cache, db
import trafaret as t
import dateutil.parser


events = Blueprint('events', __name__, url_prefix='/events/', template_folder="templates")

logger = logging.getLogger(__name__)


class EventsList(MethodView):
    template = 'events/events.html'

    def get(self):
        offset = int(request.args.get('offset', 0))
        count = int(request.args.get('count', 25))
        query = request.args.get('query', '')
        page = int(offset/count) + 1
        r = current_app.events_api.get_events(g.user.team.events_token,
                                              offset=offset,
                                              count=count,
                                              sorting='-when_start',
                                              query=query)
        events = []
        for event in r.pop('events'):
            sess = db.session()
            q = sess.query(PublishedDigest).\
                filter(PublishedDigest.events_ids.contains([int(event['id'])]))
            event['published'] = q.all()
            events.append(event)
        r['events'] = events
        return render_template(self.template,
                               events_data=r,
                               offset=offset,
                               count=count,
                               page=page,
                               query=query)

events.add_url_rule('list', view_func=login_required(EventsList.as_view('events_list')))


EVENT_CREATION_FORM = t.Dict({
                             'title': t.String,
                             'agenda': t.String,
                             'social': t.String(allow_blank=True),
                             'place': t.String(allow_blank=True),
                             'registration_url': t.URL(allow_blank=True),
                             'image_url': t.URL(allow_blank=True) | t.String(max_length=0, allow_blank=True),
                             'level': t.Enum('NONE', 'TRAINEE', 'JUNIOR', 'MIDDLE', 'SENIOR'),
                             t.Key('special', default=False): t.StrBool,
                             'when_start': t.String,
                             'when_end': t.String(allow_blank=True),
                             t.Key('include_time', to_name='only_date', default=False):
                                 t.StrBool >> (lambda x: not x),
                            }).ignore_extra('_csrf_token', 'submit')


@events.route('event/create', methods=['GET', 'POST'])
@login_required
def create_event():
    g.errors = []
    if request.method == 'POST':
        id_ = do_create_event()
        if not g.errors:
            if request.form.get('submit') == 'save_add_more':
                return redirect(url_for('events.create_event', added=1))
            return redirect(url_for('events.events_details', id_=id_))
    initial = request.form.to_dict()
    if not initial:
        initial['only_date'] = False
    return render_template('events/event_create.html', errors=g.errors,
                           initial=initial)


def do_create_event():
    try:
        data = EVENT_CREATION_FORM.check(request.form.to_dict())
        logger.info(json.dumps(data))
    except t.DataError as e:
        g.errors += ['{}: {}'.format(key, value)
                     for key, value in e.error.items()]
        return
    id_ = None
    try:
        created = current_app.events_api.add_event(g.user.team.events_token,
                                                   {'creator': g.user.username},
                                                   **data)
        id_ = created.split('/')[-1]
    except EventsServiceAPIError as e:
        g.errors += e.errors
    return id_


@events.route('details/<id_>')
@login_required
def events_details(id_):
    r = current_app.events_api.get_event(g.user.team.events_token, id_)
    return render_template('events/event_details.html',
                           event=r)


@events.route('edit/<id_>', methods=['GET', 'POST'])
@login_required
def edit_event(id_):
    r = current_app.events_api.get_event(g.user.team.events_token, id_)
    g.errors = []
    if request.method == 'POST':
        do_edit_event(id_)
        if not g.errors:
            return redirect(url_for('events.events_details', id_=id_))
    return render_template('events/event_create.html', errors=g.errors,
                           initial=r,
                           edit=True)


def do_edit_event(id_):
    try:
        data = EVENT_CREATION_FORM.check(request.form.to_dict())
    except t.DataError as e:
        g.errors += ['{}: {}'.format(key, value)
                     for key, value in e.error.items()]
        return
    try:
        current_app.events_api.edit_event(g.user.team.events_token,
                                          id_,
                                          {'creator': g.user.username},
                                          **data)
    except EventsServiceAPIError as e:
        g.errors += e.errors


@events.route('list', methods=['POST'])
def list_actions():
    if request.form['submit'] == 'delete':
        action_id = uuid.uuid4().hex
        to_delete = [k for k, v in request.form.to_dict().items() if v == 'on']
        if to_delete:
            data = {'action': 'delete', 'items': to_delete}
            cache.set(action_id, data, timeout=5*60)
            return render_template('events/approve.html', action='delete {} events'.format(len(to_delete)), action_id=action_id)
    elif request.form['submit'] == 'preview':
        events_list = [k for k, v in request.form.to_dict().items() if v == 'on']
        if events_list:
            subset_id = init_digest(events_list, {})
            set_variable(subset_id, 'template', 'main.html')  # FIXME: hardcoded
            set_variable(subset_id, 'variables', {})  # FIXME: hardcoded
            set_default_template_variables(subset_id)
            generate_preview(subset_id)
            return redirect(url_for('digestmonkey.preview_content', subset_id=subset_id))
    elif request.form['submit'] == 'approve':
        data = cache.get(request.form['action_id'])
        if not data:
            return render_template('events/error.html', errors=['Expired'])
        if data['action'] == 'delete':
            for item in data['items']:
                try:
                    current_app.events_api.delete_event(g.user.team.events_token, item)
                except EventsServiceAPIError as e:
                    return render_template('events/error.html', errors=e)

    return redirect(request.url)


from admin_service.digestmonkey.models import PublishedDigest


class SuggestedEventsList(MethodView):
    template = 'events/suggested_events.html'

    def get(self):
        events = SuggestedEvent.query.filter(SuggestedEvent.team == g.user.team.id).all()
        return render_template(self.template,
                               events=events)

events.add_url_rule('suggested/list',
                    view_func=login_required(SuggestedEventsList.as_view('suggested_events_list')))


@events.route('suggested/details/<secret>')
@login_required
def suggested_events_details(secret):
    event = SuggestedEvent.query.get(secret)
    return render_template('events/suggested_event_details.html',
                           event=event)


@events.route('suggested/accept/<secret>', methods=['GET', 'POST'])
@login_required
def accept_suggested_event(secret):
    g.errors = []
    if request.method == 'POST':
        id_ = do_create_event()
        if not g.errors:
            return redirect(url_for('events.events_details', id_=id_))

    initial = request.form.to_dict()
    event = SuggestedEvent.query.get(secret)
    initial.update(event.to_dict())
    initial['when_start'] = initial['when_start'].isoformat()
    if initial['when_end']:
        initial['when_end'] = initial['when_end'].isoformat()
    if not initial['registration_url']:
        initial['registration_url'] = ''
    return render_template('events/event_create.html', errors=g.errors,
                           initial=initial)


@events.route('suggested/decline/<secret>')
@login_required
def decline_suggested_event(secret):
    SuggestedEvent.query.filter(SuggestedEvent.secret == secret).delete()
    db.session.commit()
    return redirect(url_for('events.suggested_events_list'))


from admin_service.digestmonkey.utils.digest import init_digest, set_variable, set_default_template_variables, \
    generate_preview
