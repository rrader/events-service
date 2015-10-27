from collections import OrderedDict
from flask import g
import mailchimp


def get_mailchimp_api():
    key = g.user.team.digestmonkey_config.mailchimp_key
    return mailchimp.Mailchimp(key)


def list_list():
    lst = get_mailchimp_api().lists.list()
    return OrderedDict(sorted(
                            ((item['id'], item['name']) for item in lst['data']),
                            key=lambda x: x[1]
                             ))


def get_list(list_id):
    return get_mailchimp_api().lists.list(filters={'list_id': list_id})['data'][0]


def content(id_):
    api = get_mailchimp_api()
    return api.campaigns.content(id_)
