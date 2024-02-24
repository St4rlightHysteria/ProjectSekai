import sqlite3
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import time
from celery import Celery
from celery.schedules import crontab

from helpers import check_int, error, login_required, merge_date_time, remove_t, send_mail, parse_datetime, generate_token_by_rn, is_within_six_hours, convert_to_utc
from keys import SECRET_KEY

# users.db

"""     
CREATE TABLE tasks (user_id INTEGER, 
task_n INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
task_title TEXT NOT NULL, 
task TEXT, 
task_dt TEXT NOT NULL, 
deadline TEXT NOT NULL, 
reminders1 TEXT,
reminders2 TEXT,
reminders3 TEXT,
reminders4 TEXT,
reminders5 TEXT,
send INTEGER DEFAULT 0,
FOREIGN KEY(user_id) REFERENCES users(id));

CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
timezone TEXT,
token TEXT,  
username TEXT NOT NULL, 
hash TEXT NOT NULL,
mail TEXT,
verified INTEGER DEFAULT 0,
exp INTEGER DEFAULT 0);
"""

app = Flask(__name__, template_folder='templates', static_folder='static')

# Configure session to use filesystem (instead of signed cookies)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
app.config['SECRET_KEY'] = SECRET_KEY


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
            return render_template("register.html", notAllFields=True)

        if password != confirmation:
            return render_template("register.html", diffPaswords=True)

        if len(password) < 8 or len(password) > 32:
            return render_template("register.html", noRequirements=True)

        # Validate password requirements: letters, numbers, and special characters
        has_letters = any(char.isalpha() for char in password)
        has_numbers = any(char.isdigit() for char in password)
        has_specials = any(not char.isalnum() and char != " " for char in password)

        if not (has_letters and has_numbers and has_specials):
            return render_template("register.html", noRequirements=True)

        # Check if the username already exists
        existing_user = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing_user:
            return render_template("register.html", userExists=True)

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
            return render_template("login.html", notAllFields=True)

        user_data = db.execute("SELECT id, hash FROM users WHERE username = ?", (username,)).fetchone()
        if not user_data or not check_password_hash(user_data[1], password):  # Access hash
            return render_template("login.html", invalidCredentials=True)

        session["user_id"] = user_data[0]  # Access id using index 0
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/")
@login_required
def home():
    """Display tasks with a non-expired deadline"""

    user_id = session["user_id"]
    rn = datetime.now()

    # Fetch and filter tasks with a deadline greater than the current time
    tasks = db.execute("SELECT * FROM tasks WHERE user_id = ? AND deadline > ?", (user_id, rn)).fetchall()

    # Remove tasks with an expired deadline from the database
    db.execute("DELETE FROM tasks WHERE user_id = ? AND deadline <= ?", (user_id, rn))
    con.commit()

    return render_template("tasks.html", tasks=tasks)


@app.route("/task/<int:task_number>")
@login_required
def task_details(task_number):
    """Display details of a specific task"""

    user_id = session["user_id"]
    task = db.execute("SELECT * FROM tasks WHERE user_id = ? AND task_n = ?", (user_id, task_number)).fetchone()

    if not task:
        # Handle task not found
        return error("Task not found", 404)

    return render_template("task_details.html", task=task)


@app.route("/save_reminders/<int:task_number>", methods=["POST"])
@login_required
def save_reminders(task_number):
    # Get the reminders from the form data
    reminders = [request.form.get(f"reminder{i+1}") for i in range(5)]
    timezone = db.execute("SELECT timezone FROM users WHERE id = ?", (session['user_id'],)).fetchone()[0]

    # Update the reminders in the database
    for i, reminder_datetime in enumerate(reminders, start=1):
        reminder_column = f"reminders{i}"  # Construct the column name dynamically
        if reminder_datetime:
            reminder_datetime = convert_to_utc(remove_t(reminder_datetime), timezone)
            db.execute(f"UPDATE tasks SET {reminder_column} = ? WHERE task_n = ?", (reminder_datetime, task_number))
        else:
            db.execute(f"UPDATE tasks SET {reminder_column} = NULL WHERE task_n = ?", (task_number,))

    con.commit()

    return redirect(url_for('nft', task_number=task_number))


@app.route("/notifications/<int:task_number>", methods=["GET", "POST"])
@login_required
def nft(task_number):
    user_id = session["user_id"]

    # Fetch the task and valid_reminders from the database
    task = db.execute("SELECT * FROM tasks WHERE task_n = ?", (task_number,)).fetchone()
    reminders = [task[i + 6] for i in range(5) if task[i + 6] and task[i + 6].strip()]

    rn = datetime.utcnow()
    timezone = db.execute("SELECT timezone FROM users WHERE id = ?", (user_id,)).fetchone()[0]

    task_deadline = datetime.strptime(task[5], "%Y-%m-%d %H:%M:%S")

    # List to store valid reminders
    valid_reminders = []

    for i, r in enumerate(reminders, start=1):
        reminder_datetime = parse_datetime(remove_t(r))
        reminder_datetime = convert_to_utc(reminder_datetime, timezone)
        if reminder_datetime < rn or reminder_datetime > task_deadline:
            # Remove the reminder from the database
            db.execute(f"UPDATE tasks SET reminders{i} = NULL WHERE task_n = ? AND reminders{i} = ?", (task_number, r))
            con.commit()
            return error("Reminders cannot be before now and/or after the deadline.")
        else:
            valid_reminders.append(r)
            if r:   # store the reminder on the database if not null
                db.execute(f"UPDATE tasks SET reminders{i} = ? WHERE task_n = ? AND user_id = ?", (reminder_datetime, task_number, user_id))
                con.commit()

    return render_template("notifications.html", task=task, reminders=valid_reminders)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add task"""
    if request.method == "POST":
        rn = datetime.utcnow()  # get current UTC time

        if merge_date_time(request.form.get("date"), request.form.get("time")) <= rn:
            return error("Deadline cannot be earlier than now.")

        user_id = session["user_id"]
        timezone = db.execute("SELECT timezone FROM users WHERE id = ?", (user_id,)).fetchone()[0]

        db.execute(
            "INSERT INTO tasks(user_id, task_title, task, task_dt, deadline) VALUES(?, ?, ?, ?, ?)",
            (user_id, request.form.get("title"), request.form.get("desc"), rn,
             convert_to_utc(merge_date_time(request.form.get("date"), request.form.get("time")), timezone))
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


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/set_notifications")
@login_required
def set_nft():
    """Display tasks with a non-expired deadline"""

    user_id = session["user_id"]
    rn = datetime.utcnow()

    # Fetch and filter tasks with a deadline greater than the current time
    tasks = db.execute("SELECT * FROM tasks WHERE user_id = ? AND deadline > ?", (user_id, rn)).fetchall()

    return render_template("triggerNft.html", tasks=tasks)


@app.route("/toggle_on_task_notifications/<int:task_number>", methods=["POST"])
@login_required
def task_nft_on(task_number):
    """ Turn on a specific task's reminders' e-mails """

    user_id = session['user_id']
    tasks = db.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,)).fetchall()

    # set send column to 1 (True)
    db.execute("UPDATE tasks SET send = 1 WHERE task_n = ? AND user_id = ?", (task_number, user_id))
    con.commit()

    time.sleep(0.5)

    return render_template("TriggerNft.html", tasks=tasks)


@app.route("/toggle_off_notifications/<int:task_number>", methods=["POST"])
@login_required
def task_nft_off(task_number):
    """ Turn off a specific task's reminders' e-mails """

    user_id = session['user_id']
    tasks = db.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,)).fetchall()

    # set send column to 0 (False)
    db.execute("UPDATE tasks SET send = 0 WHERE task_n = ? AND user_id = ?", (task_number, user_id))
    con.commit()

    time.sleep(0.5)

    return render_template("TriggerNft.html", tasks=tasks)


@app.route("/verify_email", methods=["GET", "POST"])
@login_required
def verify_email():
    """Verify email by sent token and user input"""
    user_id = session['user_id']

    user_mail = db.execute("SELECT mail FROM users WHERE id = ?", (user_id,)).fetchone()
    is_verified = db.execute("SELECT verified FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user_mail:  # Mail not set
        return redirect("/set_email")
    elif is_verified[0]:  # Already verified
        return render_template("verifyEmail.html", verified=True)
    if request.method == "POST":
        token = request.form.get("token")
        database_token, token_time = db.execute("SELECT token, token_time FROM users WHERE id = ?", (user_id,)).fetchone()
        if not token or token != database_token:
            return error("Tokens do not match")
        if not is_within_six_hours(datetime.utcnow(), token_time):
            return error("Token expired", 403)

        # If tokens match and not expired, set user mail as verified and remove the token
        db.execute("UPDATE users SET verified = 1, token = NULL, token_time = NULL WHERE id = ?", (user_id,))
        con.commit()
        return render_template("verifyEmail.html", verified=True)

    return render_template("verifyEmail.html", verified=False, email=user_mail)


@app.route("/send_token", methods=["POST"])
@login_required
def send_token():
    """Store generated token and its generation time in the database"""
    user_id = session['user_id']
    token, token_time = generate_token_by_rn()
    db.execute("UPDATE users SET token = ?, token_time = ? WHERE id = ?", (token, token_time, user_id))
    con.commit()

    # send verification token
    send_mail("Haxxor Task Manager mail verification token",
              f"Heya {db.execute('SELECT username FROM users where id = ?', (user_id,)).fetchone()[0]}, here is your token:\n{token}\n Thank you for choosing HX Task Manager!",
              db.execute("SELECT mail FROM users where id = ?", (user_id,)).fetchone()[0])

    return render_template("verifyEmail.html", verified=False)


@app.route("/set_email", methods=["GET", "POST"])
@login_required
def set_email():
    """Save user mail on the database"""

    if request.method == "POST":
        user_id = session['user_id']
        user_email = request.form.get("email")

        # save user_mail on the database (not yet verified)
        db.execute("UPDATE users SET mail = ?, verified = 0 WHERE id = ?", (user_email, user_id))
        con.commit()

    return render_template("setEmail.html")


@app.route("/set_timezone", methods=["GET", "POST"])
@login_required
def set_timezone():
    """set user timezone for reminders"""

    timezone = request.form.get("timezone")     # Get user's input timezone

    if request.method == "GET" or not timezone:     # If GET method or invalid timezone
        return render_template("timezone.html")

    else:   # If POST and valid input, store timezone in database
        db.execute("UPDATE users SET timezone = ?", (timezone,))
        con.commit()
        time.sleep(0.5)
        return redirect("/")
