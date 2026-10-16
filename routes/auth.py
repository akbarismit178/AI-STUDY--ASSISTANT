from flask import Blueprint, render_template, request, redirect, flash, session
from database.db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

import os
import smtplib
from email.mime.text import MIMEText

auth = Blueprint("auth", __name__)

# ==================================================
# Gmail Configuration
# ==================================================

SENDER_EMAIL = os.getenv("MAIL_USERNAME")
APP_PASSWORD = os.getenv("MAIL_PASSWORD")


# ==================================================
# Welcome Email (Register)
# ==================================================

def send_welcome_email(user_name, user_email):

    subject = "Welcome to AI Study Assistant"

    body = f"""
Hello {user_name},

Your account has been created successfully.

Welcome to AI Study Assistant!

You can now:
- Upload PDFs
- Chat with AI
- Generate Quizzes
- Track your Progress

Happy Learning!

AI Study Assistant Team
"""

    msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = user_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()

    except Exception as e:
        print("Welcome Email Error:", e)


# ==================================================
# Login Email
# ==================================================

def send_login_email(user_name, user_email):

    subject = "Login Successful - AI Study Assistant"

    body = f"""
Hello {user_name},

You have successfully logged in to AI Study Assistant.

If this wasn't you, please change your password immediately.

Thank You,
AI Study Assistant Team
"""

    msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = user_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()

    except Exception as e:
        print("Login Email Error:", e)


# ==================================================
# Login
# ==================================================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )

        user = cursor.fetchone()

        connection.close()

        if user and check_password_hash(user[3], password):

            session["user_id"] = user[0]
            session["fullname"] = user[1]

            # Send Login Email
            send_login_email(user[1], user[2])

            flash("Login Successful!", "success")

            return redirect("/dashboard")

        flash("Invalid Email or Password!", "danger")

    return render_template("login.html")


# ==================================================
# Register
# ==================================================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:

            flash("Passwords do not match!", "danger")

            return render_template("register.html")

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )

        user = cursor.fetchone()

        if user:

            connection.close()

            flash("Email already registered!", "danger")

            return render_template("register.html")

        hashed_password = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users(fullname,email,password)
            VALUES(?,?,?)
            """,
            (
                fullname,
                email,
                hashed_password
            )
        )

        connection.commit()
        connection.close()

        # Send Welcome Email
        send_welcome_email(fullname, email)

        flash("Registration Successful! Please Login.", "success")

        return redirect("/login")

    return render_template("register.html")




# ==================================================
# Logout
# ==================================================

@auth.route("/logout")
def logout():

    session.clear()

    flash("Logged Out Successfully!", "success")

    return redirect("/login")