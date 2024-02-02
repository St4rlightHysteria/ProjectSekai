import os
import sqlite3
from json import dumps, loads
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import time

from helpers import checkInt, error, login_required, merge_date_time, secret_key

# users.db

"""     
CREATE TABLE tasks (user_id INTEGER, 
task_n INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
task_title TEXT NOT NULL, 
task TEXT, 
task_dt TEXT NOT NULL, 
deadline TEXT NOT NULL, 
reminders TEXT,
FOREIGN KEY(user_id) REFERENCES users(id));

CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
token TEXT,  
username TEXT NOT NULL, 
hash TEXT NOT NULL,
exp INTEGER DEFAULT 0);
"""

app = Flask(__name__, template_folder='templates', static_folder='static')

# Configure session to use filesystem (instead of signed cookies)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

app.config['SECRET_KEY'] = secret_key

# Set database
con = sqlite3.connect("users.db", check_same_thread=False)
db = con.cursor()


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register"""
    session.clear()

    if request.method == "POST":
        # Validate input fields
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not (username and password and confirmation):
            return error("All fields are required", 403)

        if password != confirmation:
            return error("Passwords do not match", 403)

        if len(password) < 8 or len(password) > 32:
            return error("Password length should be between 8 and 32 characters", 403)

        # Validate password requirements: letters, numbers, and special characters
        has_letters = any(char.isalpha() for char in password)
        has_numbers = any(char.isdigit() for char in password)
        has_specials = any(not char.isalnum() and char != " " for char in password)

        if not (has_letters and has_numbers and has_specials):
            return error("Password does not meet the requirements", 403)

        # Check if the username already exists
        existing_user = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing_user:
            return error("Username already exists", 403)

        # Insert the new user into the database
        hashed_password = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (username, hashed_password))
        con.commit()

        return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not (username and password):
            return error("Username and password are required", 403)

        user_data = db.execute("SELECT id, hash FROM users WHERE username = ?", (username,)).fetchone()
        if not user_data or not check_password_hash(user_data[1], password):  # Access hash using index 4
            return error("Invalid username and/or password", 403)

        session["user_id"] = user_data[0]  # Access id using index 0
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/")
@login_required
def home():
    """ display all tasks """
    user_id = session["user_id"]
    tasks = db.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,)).fetchall()

    return render_template("tasks.html", tasks=tasks)


@app.route("/task/<int:task_number>")
@login_required
def task_details(task_number):
    """Display details of a specific task"""

    user_id = session["user_id"]
    task = db.execute("SELECT * FROM tasks WHERE user_id = ? AND task_n = ?", (user_id, task_number)).fetchone()

    if not task:
        # Handle task not found
        return error("Task not found", 400)

    return render_template("task_details.html", task=task)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add task"""
    if request.method == "POST":
        rn = datetime.now()  # get current time

        if merge_date_time(request.form.get("date"), request.form.get("time")) <= rn:
            return error("Deadline cannot be earlier than now.")

        user_id = session["user_id"]

        db.execute(
            "INSERT INTO tasks(user_id, task_title, task, task_dt, deadline) VALUES(?, ?, ?, ?, ?)",
            (user_id, request.form.get("title"), request.form.get("desc"), rn,
             merge_date_time(request.form.get("date"), request.form.get("time")))
        )

        # add 5 exp points for adding a task
        db.execute("UPDATE users SET exp = exp + 5 WHERE id = ?", (user_id,))

        con.commit()

        return redirect("/")

    else:
        return render_template("add.html")


@app.route("/delete_task/<int:task_number>", methods=["POST"])
@login_required
def delete_task(task_number):
    """ Delete a specific task """

    user_id = session['user_id']
    db.execute("DELETE FROM tasks WHERE user_id = ? AND task_n = ?", (user_id, task_number))

    # remove 5 exp for deleting a task
    db.execute("UPDATE users SET exp = CASE WHEN exp >= 5 THEN exp - 5 ELSE 0 END WHERE id = ?", (user_id,))

    con.commit()

    return redirect('/')

@app.route("/task_notifications/<int:task_number>", methods=["GET", "POST"])
@login_required
def task_nft(task_number):

    task = db.execute("SELECT * FROM tasks WHERE task_n = ?", (task_number,)).fetchone()
    return render_template("task_nft.html", task=task)

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/notifications")
@login_required
def nft():
    """ display all tasks """
    user_id = session["user_id"]
    tasks = db.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,)).fetchall()

    return render_template("nft_time.html", tasks=tasks)

@app.route("/level")
@login_required
def lvl():
    user_id = session['user_id']
    exp = db.execute("SELECT exp FROM users WHERE id = ?", (user_id,)).fetchone()[0]
    return render_template("level.html", user_exp=exp)
