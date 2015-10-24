from flask import current_app
from hashlib import md5


def hash_password(password):
    return str(md5(password.encode() + current_app.config['SECRET_KEY']))
