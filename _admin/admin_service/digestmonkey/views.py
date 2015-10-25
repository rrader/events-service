# -*- coding: utf-8 -*-
import uuid
import dateutil

from flask import (Blueprint, render_template, g, request, url_for,
    current_app, send_from_directory, json, redirect, make_response, abort)

from flask.ext.login import login_required
from admin_service.events.client import EventsServiceAPIError

from ..extensions import pages, csrf, cache
import trafaret as t

digestmonkey = Blueprint('digestmonkey', __name__, url_prefix='/digestmonkey/', template_folder="templates")


@digestmonkey.route('index')
@login_required
def index():
    return render_template('digestmonkey/index.html')
