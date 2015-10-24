# -*- coding: utf-8 -*-

from flask import (Blueprint, render_template, g, request, url_for,
    current_app, send_from_directory, json, redirect, make_response, abort)

from flask.ext.login import login_required

from ..extensions import pages, csrf

events = Blueprint('events', __name__, template_folder="templates")
