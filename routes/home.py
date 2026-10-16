from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    request,
    flash
)

from database.db import get_db_connection

import os
import smtplib

from email.message import EmailMessage
from dotenv import load_dotenv


# =========================
# Load Environment Variables
# =========================

load_dotenv()


home = Blueprint("home", __name__)


# =========================
# Home
# =========================

@home.route("/")
def index():

    connection = get_db_connection()
    cursor = connection.cursor()

    # =========================
    # Total Registered Students
    # =========================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM users
        """
    )

    student_count = cursor.fetchone()[0]


    # =========================
    # Total Study Materials
    # =========================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM study_materials
        """
    )

    material_count = cursor.fetchone()[0]


    connection.close()


    return render_template(
        "index.html",
        student_count=student_count,
        material_count=material_count
    )


# =========================
# Get Started
# =========================

@home.route("/get-started")
def get_started():

    if "user_id" in session:
        return redirect("/dashboard")

    return redirect("/login")


# =========================
# About
# =========================

@home.route("/about")
def about():

    return render_template("about.html")


# =========================
# Features
# =========================

@home.route("/features")
def features():

    return render_template("features.html")


# =========================
# Contact
# =========================

@home.route("/contact", methods=["GET", "POST"])
def contact():

    # =========================
    # Show Contact Page
    # =========================

    if request.method == "GET":

        return render_template("contact.html")


    # =========================
    # Get Form Data
    # =========================

    name = request.form.get(
        "name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    subject = request.form.get(
        "subject",
        ""
    ).strip()

    message = request.form.get(
        "message",
        ""
    ).strip()


    # =========================
    # Validation
    # =========================

    if not name or not email or not subject or not message:

        flash(
            "Please fill all fields.",
            "danger"
        )

        return redirect("/contact")


    # =========================
    # Save Message to Database
    # =========================

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO contact_messages
            (
                name,
                email,
                subject,
                message
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                email,
                subject,
                message
            )
        )

        connection.commit()

    except Exception as e:

        connection.rollback()

        print(
            "CONTACT DATABASE ERROR:"
        )

        print(
            repr(e)
        )

        connection.close()

        flash(
            "Unable to send your message. Please try again.",
            "danger"
        )

        return redirect("/contact")

    finally:

        connection.close()


    # =========================
    # Send Gmail Notification
    # =========================

    try:

        sender_email = os.getenv(
            "MAIL_USERNAME"
        )

        app_password = os.getenv(
            "MAIL_PASSWORD"
        )

        receiver_email = os.getenv(
            "MAIL_RECEIVER"
        )


        # Check Email Configuration

        if (
            not sender_email
            or not app_password
            or not receiver_email
        ):

            raise ValueError(
                "Email configuration is missing in .env"
            )


        # Create Email

        mail = EmailMessage()


        mail["Subject"] = (
            f"New Contact Message: {subject}"
        )

        mail["From"] = sender_email

        mail["To"] = receiver_email


        mail.set_content(
            f"""
New Contact Message
===================

Name:
{name}

Email:
{email}

Subject:
{subject}

Message:
{message}

===================
AI Study Assistant
"""
        )


        # Connect to Gmail SMTP

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as smtp:

            smtp.login(
                sender_email,
                app_password
            )

            smtp.send_message(
                mail
            )


        print(
            "CONTACT EMAIL SENT SUCCESSFULLY"
        )


    except Exception as e:

        # Email failure should NOT
        # delete the database message.

        print(
            "CONTACT EMAIL ERROR:"
        )

        print(
            repr(e)
        )


    # =========================
    # Success
    # =========================

    flash(
        "✅ Your message has been sent successfully!",
        "success"
    )


    return redirect("/contact")