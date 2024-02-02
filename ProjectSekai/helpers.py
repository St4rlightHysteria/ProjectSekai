import os
import csv
from datetime import datetime
import pytz
import requests
import subprocess
import urllib
import uuid
import secrets

from flask_mail import Message, Mail
from flask import redirect, render_template, session
from functools import wraps


# setx SECRET_KEY "e5bb0fe1690eee18ae7a20a1ad32b740164724279eeb4403"
secret_key = "e5bb0fe1690eee18ae7a20a1ad32b740164724279eeb4403"
email_pass = "KianaKaslana1"

def generate_token():
    return secrets.token_hex(16)  # Generate a hex token of 16 bytes

def escape(s):
    """
    Escape special characters.

    https://github.com/jacebrowning/memegen#special-characters
    """
    for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                     ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
        s = s.replace(old, new)
    return s

def checkInt(field):
    """if field is only numeric"""

    for s in field:
        if not s.isnumeric():
            return False

    return True

def error(msg, code=400):
    return render_template("error.html", img=f"https://api.memegen.link/images/ugandanknuck/{escape(msg)}/{code}_.png")

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def merge_date_time(date_str, time_str):
    # Convert the strings to date and time objects
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    time_obj = datetime.strptime(time_str, '%H:%M').time()

    # Combine the date and time objects into a datetime object
    datetime_obj = datetime.combine(date_obj, time_obj)

    return datetime_obj

