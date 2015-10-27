# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, request, current_app, g, flash, url_for
from flask.ext.login import login_required, logout_user, login_user
from flask.ext.babel import gettext as _
from sqlalchemy.orm.exc import NoResultFound
from admin_service.auth.utils import hash_password, admin_required
from .models import User, Team
from ..extensions import db
from .forms import SettingsForm
import trafaret as t
from trafaret.extras import KeysSubset


auth = Blueprint('auth', __name__, url_prefix='/auth/', template_folder="templates")


@auth.route('login', methods=['GET', 'POST'])
def login():
    errors = []
    if request.method == 'POST':
        errors += do_login()
        if not errors:
            return redirect(url_for('auth.profile'))
    return render_template('auth/index.html', errors=errors)


def do_login():
    try:
        user = User.query.filter(User.username == request.form['username']).one()
    except NoResultFound:
        return ['User not found']
    if user.password != hash_password(request.form['password']):
        return ['Wrong password']
    login_user(user)
    return []


CHANGE_PASSWORD_FORM = t.Dict({'oldpassword': t.String(allow_blank=True) >> (lambda x: x if hash_password(x) == g.user.password
                                                                     else t.DataError('Wrong old password')),
                                KeysSubset('password1', 'password2'):
                                 (lambda x:
                                  {'password': hash_password(x['password1'])
                                   if x['password1'] == x['password2']
                                   else t.DataError('Passwords does not match')
                                   })
                                }).ignore_extra('_csrf_token', 'submit')

@auth.route('profile', methods=['GET', 'POST'])
@login_required
def profile():
    g.errors = []
    message = None
    if request.method == 'POST':
        if request.form['submit'] == 'change_password':
            do_change_password()
            if not g.errors:
                message = 'Password changed'
    return render_template('auth/profile.html', errors=g.errors,
                           message=message)


def do_change_password():
    try:
        data = CHANGE_PASSWORD_FORM.check(request.form.to_dict())
    except t.DataError as e:
        g.errors += ['{}: {}'.format(key, value)
                     for key, value in e.error.items()]
        return
    sess = db.session()
    g.user.password = data['password']
    sess.add(g.user)
    sess.commit()


@auth.route('logout')
def logout():
    logout_user()
    return redirect('/')


@auth.route('teams')
@login_required
@admin_required
def teams():
    teams = Team.query.all()
    return render_template('auth/teams.html', teams=teams)


@auth.route('teams/<id_>')
@login_required
@admin_required
def team(id_):
    team = Team.query.get(id_)
    return render_template('auth/team.html', team=team)


@auth.route('teams/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_team():
    g.errors = []
    if request.method == 'POST':
        team = do_create_team()
        if not g.errors:
            return redirect(url_for('auth.team', id_=team.id))
    return render_template('auth/team_create.html', errors=g.errors)


TEAM_CREATION_FORM = t.Dict({'name': t.String}).ignore_extra('_csrf_token')


def do_create_team():
    try:
        data = TEAM_CREATION_FORM.check(request.form.to_dict())
    except t.DataError as e:
        g.errors += ['{}: {}'.format(key, value)
                     for key, value in e.error.items()]
        return
    events_key = current_app.events_api.register_provider(data['name'])
    data['events_token'] = events_key
    sess = db.session()
    team = Team(**data)
    sess.add(team)
    sess.commit()
    return team


@auth.route('user/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    g.errors = []
    if request.method == 'POST':
        user = do_create_user()
        if not g.errors:
            return redirect(url_for('auth.team', id_=user.team_id))
    default_team = request.args.get('team')
    if default_team is not None:
        default_team = int(default_team)
    return render_template('auth/user_create.html', errors=g.errors,
                           teams=Team.query.all(),
                           default_team=default_team)


USER_CREATION_FORM = t.Dict({
                             'username': t.String >>
                                 (lambda username:
                                  username
                                  if not db.session().query(
                                  User.query.filter(User.username == username).exists()).scalar()
                                  else t.DataError('User with same username is already exists')),
                             'name': t.String,
                             'email': t.Email,
                             'team': t.Int >>
                                 (lambda team_id:
                                  Team.query.get(team_id)
                                  if db.session().query(
                                     Team.query.filter(Team.id == team_id).exists()).scalar()
                                  else t.DataError('Team does not exists')
                                  ),
                             KeysSubset('password1', 'password2'):
                                 (lambda x:
                                  {'password': hash_password(x['password1'])
                                   if x['password1'] == x['password2']
                                   else t.DataError('Passwords does not match')
                                   })
                             }).ignore_extra('_csrf_token')


def do_create_user():
    try:
        data = USER_CREATION_FORM.check(request.form.to_dict())
    except t.DataError as e:
        g.errors += ['{}: {}'.format(key, value)
                     for key, value in e.error.items()]
        return
    sess = db.session()
    user = User(**data)
    sess.add(user)
    sess.commit()
    return user
