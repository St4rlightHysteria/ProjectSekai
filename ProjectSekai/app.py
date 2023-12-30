import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message
from datetime import datetime

from helpers import checkInt, error, login_required, merge_date_time

app = Flask(__name__, template_folder='templates', static_folder='static')
mail = Mail(app)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set database
con = sqlite3.connect("users.db", check_same_thread=False)
db = con.cursor()

def send_email(recipient, subject, body):
    msg = Message(subject, recipients=[recipient])
    msg.body = body
    mail.send(msg)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/register", methods=["GET", "POST"])
def register():
    """register"""

    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return error("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return error("must provide password", 403)

        elif not request.form.get("confirmation"):
            return error("must confirm password", 403)

        elif request.form.get("password") != request.form.get("confirmation"):
            return error("Passwords do not match", 403)

        if len(request.form.get("password")) < 8 or len(request.form.get("password")) > 32:
            return render_template("register.html")

        else:

            chars = {"letters": 0,
                     "numbers": 0,
                     "specials": 0}

            for s in request.form.get("password"):

                if not ((str(s).isalpha()) or (str(s)).isnumeric() or str(s) == " "):
                    chars["specials"] += 1
                elif str(s).isalpha():
                    chars["letters"] += 1
                elif (str(s)).isnumeric():
                    chars["numbers"] += 1

                if 0 not in chars.values():
                    break

        if 0 in chars.values():
            return error("Password does not meet the requirements", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"))).fetchall()

        # Ensure username doesn't exist
        if len(rows) >= 1:
            return error("Username already exists", 403)

        hashed_password = generate_password_hash(request.form.get("password"))

        db.execute("INSERT INTO users(username, hash) VALUES(?, ?)", (request.form.get("username"), hashed_password))
        con.commit()

        return redirect("/login")

    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return error("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return error("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),)).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return error("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Update database user ID
        db.execute("UPDATE users SET id = ? WHERE username = ?", (session["user_id"], request.form.get("username")))
        con.commit()
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/")
@login_required
def index():
    return render_template("tasks.html")

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """ add task """
    if request.method == "POST":
        rn = datetime.now()     # get time right now.

        # check if fields are good
        if request.form.get("title") is None:
            return error("Task title is empty bruh")
        elif request.form.get("date") is None:
            return error("Insert a deadline date bruh")
        elif request.form.get("time") is None:
            return error("Insert a deadline time bruh")
        elif request.form.get("desc") is None:
            return error("Insert your task description")
        elif merge_date_time(request.form.get("date"), request.form.get("time")) <= rn:
            return error("Deadline cannot be earlier than now.")

        

@app.route("/error")
def err():
    return error("error", 400)

