from _md5 import md5
from flask_script import Command, Manager, prompt_pass, Option
from flask import current_app
from admin_service.auth.models import Team, User
from admin_service.auth.utils import hash_password
from admin_service.events.client import EventsServiceAPI
from admin_service.extensions import db

AuthCommand = Manager(usage='Auth tools')


class CreateAdmin(Command):

    def get_options(self):
        return (
            Option('--password',
                   dest='password',
                   default='1111'),
        )

    def run(self, password):
        team = self.get_team()

        sess = db.session()
        has_admin = sess.query(User.query.filter(User.username == 'admin').
                               exists()).scalar()
        if not has_admin:
            user = User(username='admin', password=hash_password(password),
                        admin=True, team_id=team.id)
            sess.add(user)
            sess.commit()
        else:
            print("User admin is already exists")

    def get_team(self):
        sess = db.session()
        has_default_team = sess.query(Team.query.filter(Team.name == 'default').
                                      exists()).scalar()
        if not has_default_team:
            print("Creating default Team")
            team = Team(name='default',
                        events_token='424242')
            sess.add(team)
            sess.commit()
        else:
            team = Team.query.filter(Team.name == 'default').one()
        return team


AuthCommand.add_command('create_admin', CreateAdmin)
