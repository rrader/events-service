from functools import wraps
from flask import current_app, g, request, redirect, url_for, render_template
from hashlib import sha1
import trafaret as t


def hash_password(password):
    return sha1(password.encode() + current_app.config['SECRET_KEY']).hexdigest()


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        if not g.user.is_admin:
            return render_template('misc/403.html')
        return f(*args, **kwargs)
    return decorated_function
