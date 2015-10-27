import dateutil
from flask import g
from github import Github
import jinja2
from admin_service.extensions import cache


def get_github_repo():
    key = g.user.team.digestmonkey_config.github_key
    repo = g.user.team.digestmonkey_config.templates_uri
    return Github(key).get_repo(repo)


def configure_filters(env):
    def datetimeformat(date, format='%H:%M / %d-%m-%Y'):
        date = dateutil.parser.parse(date)
        native = date.replace(tzinfo=None)
        return native.strftime(format)
    env.filters['date'] = datetimeformat

    def slice(val, start, end):
        return val[start:end]
    env.filters['slice'] = slice


def format_template(name, variables):
    repo = get_github_repo()
    template_env = jinja2.Environment(loader=GitHubLoader(repo))
    configure_filters(template_env)
    template = template_env.get_template(name)
    return template.render(**variables)


class GitHubLoader(jinja2.BaseLoader):
    def __init__(self, repo):
        self.repo = repo

    @cache.memoize(30)
    def get_source(self, environment, template):
        print('> ' + template)
        content = self.repo.get_file_contents(template).decoded_content.decode()
        return content, template, None
