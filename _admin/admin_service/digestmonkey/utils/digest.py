from collections import defaultdict
import uuid
import dateutil.parser
from flask import current_app, json, g
from admin_service.digestmonkey.github_utils import get_github_repo, format_template
from admin_service.extensions import cache


def init_digest(events_list, params):
    """
    Step 1: create initial data for digest
    """
    events_list = [get_event(k) for k in events_list]
    subset_id = uuid.uuid4().hex
    query_params = params
    cache.set(subset_id,
              {'list': events_list,
               'query_params': query_params
               }, timeout=60 * 60 * 24)
    return subset_id


def set_default_template_variables(subset_id):
    """
    Step 2: Retrieve default variables from Github
    """
    data = cache.get(subset_id)
    variables = json.loads(
        get_github_repo().get_file_contents("/{}.defaults".format(data['template'])). \
            decoded_content.decode()
    )
    params = defaultdict(str, data['query_params'])
    for key, value in variables.items():
        variables[key] = value.format(**params)
    variables.update(data.get('variables', {}))
    return variables


def generate_preview(subset_id):
    """
    Step 3: Generate HTML Preview based on chosen parameters
    """
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
    cache.set(subset_id, data, timeout=60 * 60 * 24)
    return preview


# UTILS

def get_event(id_):
    return current_app.events_api.get_event(g.user.team.events_token, id_)


def set_variable(subset_id, key, value, timeout=60 * 60 * 24):
    data = cache.get(subset_id)
    data[key] = value
    cache.set(subset_id, data, timeout=timeout)

def sorted_eventslist(elist):
    return sorted(elist, key=lambda e: dateutil.parser.parse(e['when_start']))
