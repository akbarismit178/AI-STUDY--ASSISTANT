from flask import Blueprint, render_template, request, redirect, session, flash ,send_from_directory , current_app
from database.db import get_db_connection
from werkzeug.security import check_password_hash
from utils.path_resolver import resolve_path
import os


admin = Blueprint("admin", __name__)


# =====================================================
# ADMIN LOGIN
# =====================================================

@admin.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    
    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, fullname, email, password
            FROM admins
            WHERE email = ?
            """,
            (email,)
        )

        admin_user = cursor.fetchone()

        connection.close()

        # Check admin credentials
        if admin_user and check_password_hash(
            admin_user[3],
            password
        ):

            session["admin_id"] = admin_user[0]
            session["admin_name"] = admin_user[1]
            session["admin_email"] = admin_user[2]

            flash(
                "Admin Login Successful!",
                "success"
            )

            return redirect("/admin")

        flash(
            "Invalid Admin Email or Password!",
            "danger"
        )

    return render_template(
        "admin/admin_login.html"
    )


# =====================================================
# ADMIN DASHBOARD
# =====================================================

@admin.route("/admin")
def admin_dashboard():

    # Login Check
    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor()

    # =========================
    # Total Users
    # =========================

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    total_users = cursor.fetchone()[0]


    # =========================
    # Total PDFs
    # =========================

    cursor.execute(
        "SELECT COUNT(*) FROM pdfs"
    )

    total_pdfs = cursor.fetchone()[0]


    # =========================
    # Total AI Chats
    # =========================

    cursor.execute(
        "SELECT COUNT(*) FROM chat_history"
    )

    total_chats = cursor.fetchone()[0]


    # =========================
    # Total Quizzes
    # =========================

    cursor.execute(
        "SELECT COUNT(*) FROM quizzes"
    )

    total_quizzes = cursor.fetchone()[0]


    # =========================
    # Total Study Materials
    #
    # Uploaded PDFs = Study Materials
    # =========================

    cursor.execute(
        "SELECT COUNT(*) FROM study_materials"
    )

    total_materials = cursor.fetchone()[0]


    connection.close()


    return render_template(
        "admin/admin_dashboard.html",
        total_users=total_users,
        total_pdfs=total_pdfs,
        total_chats=total_chats,
        total_quizzes=total_quizzes,
        total_materials=total_materials
    )


# =====================================================
# USERS MANAGEMENT
# =====================================================

@admin.route("/admin/users")
def admin_users():

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, fullname, email
        FROM users
        ORDER BY id DESC
        """
    )

    users = cursor.fetchall()

    connection.close()


    return render_template(
        "admin/admin_users.html",
        users=users
    )


# =====================================================
# DELETE USER
# =====================================================

@admin.route(
    "/admin/users/delete/<int:user_id>",
    methods=["POST"]
)
def delete_user(user_id):

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # =========================
        # Delete Chat History
        # =========================

        cursor.execute(
            """
            DELETE FROM chat_history
            WHERE user_id = ?
            """,
            (user_id,)
        )


        # =========================
        # Delete Quizzes
        # =========================

        cursor.execute(
            """
            DELETE FROM quizzes
            WHERE user_id = ?
            """,
            (user_id,)
        )


        # =========================
        # Delete PDFs
        # =========================

        # Get PDF files first
        cursor.execute(
            """
            SELECT file_path
            FROM pdfs
            WHERE user_id = ?
            """,
            (user_id,)
        )

        user_pdfs = cursor.fetchall()


        # Delete actual PDF files
        for pdf in user_pdfs:

            file_path = resolve_path(pdf[0])

            if file_path and os.path.exists(file_path):

                try:
                    os.remove(file_path)

                except OSError:
                    pass


        # Delete PDF records
        cursor.execute(
            """
            DELETE FROM pdfs
            WHERE user_id = ?
            """,
            (user_id,)
        )


        # =========================
        # Delete Progress
        # =========================

        cursor.execute(
            """
            DELETE FROM progress
            WHERE user_id = ?
            """,
            (user_id,)
        )


        # =========================
        # Delete User
        # =========================

        cursor.execute(
            """
            DELETE FROM users
            WHERE id = ?
            """,
            (user_id,)
        )


        connection.commit()


        flash(
            "User deleted successfully!",
            "success"
        )


    except Exception as e:

        connection.rollback()

        flash(
            f"Error deleting user: {e}",
            "danger"
        )


    finally:

        connection.close()


    return redirect("/admin/users")


# =====================================================
# PDF MANAGEMENT
# =====================================================

@admin.route("/admin/pdfs")
def admin_pdfs():

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            pdfs.id,
            pdfs.pdf_name,
            pdfs.upload_date,
            pdfs.file_path,
            users.fullname,
            users.email

        FROM pdfs

        LEFT JOIN users
        ON pdfs.user_id = users.id

        ORDER BY pdfs.id DESC
        """
    )

    pdfs = cursor.fetchall()

    connection.close()


    return render_template(
        "admin/admin_pdfs.html",
        pdfs=pdfs
    )


# =====================================================
# ADMIN DELETE PDF
# =====================================================

@admin.route(
    "/admin/pdfs/delete/<int:pdf_id>",
    methods=["POST"]
)
def admin_delete_pdf(pdf_id):

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # =========================
        # Get PDF File Path
        # =========================

        cursor.execute(
            """
            SELECT file_path
            FROM pdfs
            WHERE id = ?
            """,
            (pdf_id,)
        )

        pdf = cursor.fetchone()


        if not pdf:

            flash(
                "PDF not found!",
                "danger"
            )

            connection.close()

            return redirect("/admin/pdfs")


        file_path = resolve_path(pdf[0])


        # =========================
        # Delete Actual PDF File
        # =========================

        if file_path and os.path.exists(file_path):

            try:
                os.remove(file_path)

            except OSError:
                pass


        # =========================
        # Delete Database Record
        # =========================

        cursor.execute(
            """
            DELETE FROM pdfs
            WHERE id = ?
            """,
            (pdf_id,)
        )


        connection.commit()


        flash(
            "PDF deleted successfully!",
            "success"
        )


    except Exception as e:

        connection.rollback()

        flash(
            f"Error deleting PDF: {e}",
            "danger"
        )


    finally:

        connection.close()


    return redirect("/admin/pdfs")

# =====================================================
# QUIZ MANAGEMENT
# =====================================================

@admin.route("/admin/quizzes")
def admin_quizzes():

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            quizzes.id,
            quizzes.title,
            quizzes.score,
            quizzes.total_questions,
            quizzes.correct_answers,
            quizzes.wrong_answers,
            quizzes.percentage,
            quizzes.created_at,
            quizzes.pdf_name,
            users.fullname,
            users.email

        FROM quizzes

        LEFT JOIN users
        ON quizzes.user_id = users.id

        ORDER BY quizzes.id DESC
        """
    )

    quizzes = cursor.fetchall()

    connection.close()

    return render_template(
        "admin/admin_quizzes.html",
        quizzes=quizzes
    )


# =====================================================
# DELETE QUIZ
# =====================================================

@admin.route(
    "/admin/quizzes/delete/<int:quiz_id>",
    methods=["POST"]
)
def admin_delete_quiz(quiz_id):

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT id
            FROM quizzes
            WHERE id = ?
            """,
            (quiz_id,)
        )

        quiz = cursor.fetchone()

        if not quiz:

            flash(
                "Quiz not found!",
                "danger"
            )

            connection.close()

            return redirect("/admin/quizzes")


        cursor.execute(
            """
            DELETE FROM quizzes
            WHERE id = ?
            """,
            (quiz_id,)
        )

        connection.commit()

        flash(
            "Quiz deleted successfully!",
            "success"
        )

    except Exception as e:

        connection.rollback()

        flash(
            f"Error deleting quiz: {e}",
            "danger"
        )

    finally:

        connection.close()

    return redirect("/admin/quizzes")

# =====================================================
# AI CHAT MANAGEMENT
# =====================================================

@admin.route("/admin/chats")
def admin_chats():

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            chat_history.id,
            chat_history.question,
            chat_history.answer,
            chat_history.created_at,
            users.fullname,
            users.email

        FROM chat_history

        LEFT JOIN users
        ON chat_history.user_id = users.id

        ORDER BY chat_history.id DESC
        """
    )

    chats = cursor.fetchall()

    connection.close()

    return render_template(
        "admin/admin_chats.html",
        chats=chats
    )


# =====================================================
# DELETE AI CHAT
# =====================================================

@admin.route(
    "/admin/chats/delete/<int:chat_id>",
    methods=["POST"]
)
def admin_delete_chat(chat_id):

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT id
            FROM chat_history
            WHERE id = ?
            """,
            (chat_id,)
        )

        chat = cursor.fetchone()

        if not chat:

            flash(
                "Chat not found!",
                "danger"
            )

            connection.close()

            return redirect("/admin/chats")


        cursor.execute(
            """
            DELETE FROM chat_history
            WHERE id = ?
            """,
            (chat_id,)
        )

        connection.commit()

        flash(
            "AI Chat deleted successfully!",
            "success"
        )

    except Exception as e:

        connection.rollback()

        flash(
            f"Error deleting chat: {e}",
            "danger"
        )

    finally:

        connection.close()

    return redirect("/admin/chats")


# =====================================================
# STUDY MATERIALS MANAGEMENT
# =====================================================

@admin.route("/admin/study-materials")
def admin_study_materials():

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            study_materials.id,
            study_materials.title,
            study_materials.description,
            study_materials.file_path,
            study_materials.created_at,
            users.fullname,
            users.email

        FROM study_materials

        LEFT JOIN users
        ON study_materials.user_id = users.id

        ORDER BY study_materials.id DESC
        """
    )

    materials = cursor.fetchall()

    connection.close()

    return render_template(
        "admin/admin_study_materials.html",
        materials=materials
    )

# =====================================================
# VIEW STUDY MATERIAL
# =====================================================

@admin.route("/admin/study-materials/view/<int:material_id>")
def admin_view_study_material(material_id):

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT file_path
        FROM study_materials
        WHERE id = ?
        """,
        (material_id,)
    )

    material = cursor.fetchone()

    connection.close()

    if not material:
        return "Study Material not found.", 404

    file_path = material[0]

    if not file_path:
        return "No file attached to this Study Material.", 404

    # Normalize Windows path
    file_path = file_path.replace("\\", "/").lstrip("/")

    # =================================================
    # CASE 1: Old uploaded PDF
    # uploads/filename.pdf
    # =================================================

    if file_path.startswith("uploads/"):

        relative_path = file_path[len("uploads/"):]

        upload_folder = os.path.join(
            current_app.root_path,
            "uploads"
        )

        full_path = os.path.join(
            upload_folder,
            relative_path
        )

        print("========================================")
        print("TYPE: UPLOADS")
        print("FILE PATH FROM DB:", material[0])
        print("FULL FILE PATH:", full_path)
        print("FILE EXISTS:", os.path.isfile(full_path))
        print("========================================")

        if not os.path.isfile(full_path):
            return "PDF file not found on server.", 404

        return send_from_directory(
            upload_folder,
            relative_path
        )

    # =================================================
    # CASE 2: New Study Material
    # static/study_materials/filename.pdf
    # =================================================

    if file_path.startswith("static/"):

        file_path = file_path[len("static/"):]

    static_folder = current_app.static_folder

    full_path = os.path.join(
        static_folder,
        file_path
    )

    print("========================================")
    print("TYPE: STATIC")
    print("FILE PATH FROM DB:", material[0])
    print("FULL FILE PATH:", full_path)
    print("FILE EXISTS:", os.path.isfile(full_path))
    print("========================================")

    if not os.path.isfile(full_path):
        return "PDF file not found on server.", 404

    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)

    return send_from_directory(
        os.path.join(
            static_folder,
            directory
        ),
        filename
    )

# =====================================================
# DELETE STUDY MATERIAL
# =====================================================

@admin.route(
    "/admin/study-materials/delete/<int:material_id>",
    methods=["POST"]
)
def admin_delete_study_material(material_id):

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # -------------------------------------------------
        # Get material
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT file_path
            FROM study_materials
            WHERE id = ?
            """,
            (material_id,)
        )

        material = cursor.fetchone()

        if not material:

            flash(
                "Study Material not found.",
                "danger"
            )

            return redirect("/admin/study-materials")


        file_path = material[0]


        # -------------------------------------------------
        # Delete database record
        # -------------------------------------------------

        cursor.execute(
            """
            DELETE FROM study_materials
            WHERE id = ?
            """,
            (material_id,)
        )

        connection.commit()


        # -------------------------------------------------
        # Delete physical file if it exists
        # -------------------------------------------------

        if file_path:

            file_path = file_path.replace("\\", "/")

            if file_path.startswith("/"):
                file_path = file_path[1:]

            if file_path.startswith("static/"):
                file_path = file_path[len("static/"):]

            static_folder = os.path.join(
                admin.root_path,
                "..",
                "static"
            )

            static_folder = os.path.abspath(
                static_folder
            )

            physical_file = os.path.join(
                static_folder,
                file_path
            )

            if os.path.isfile(physical_file):

                os.remove(physical_file)


        flash(
            "Study Material deleted successfully.",
            "success"
        )


    except Exception as e:

        connection.rollback()

        print(
            "DELETE STUDY MATERIAL ERROR:"
        )

        print(repr(e))

        flash(
            "Error deleting Study Material.",
            "danger"
        )


    finally:

        connection.close()


    return redirect("/admin/study-materials")

# =====================================================
# CONTACT MESSAGES
# =====================================================

@admin.route("/admin/contact-messages")
def admin_contact_messages():

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            email,
            subject,
            message,
            created_at
        FROM contact_messages
        ORDER BY id DESC
        """
    )

    messages = cursor.fetchall()

    connection.close()

    return render_template(
        "admin/admin_contact_messages.html",
        messages=messages
    )


# =====================================================
# DELETE CONTACT MESSAGE
# =====================================================

@admin.route(
    "/admin/contact-messages/delete/<int:message_id>",
    methods=["POST"]
)
def admin_delete_contact_message(message_id):

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT id
            FROM contact_messages
            WHERE id = ?
            """,
            (message_id,)
        )

        message = cursor.fetchone()

        if not message:

            flash(
                "Contact message not found!",
                "danger"
            )

            return redirect("/admin/contact-messages")


        cursor.execute(
            """
            DELETE FROM contact_messages
            WHERE id = ?
            """,
            (message_id,)
        )

        connection.commit()

        flash(
            "Contact message deleted successfully!",
            "success"
        )

    except Exception as e:

        connection.rollback()

        flash(
            f"Error deleting message: {e}",
            "danger"
        )

    finally:

        connection.close()

    return redirect("/admin/contact-messages")

# =====================================================
# ADMIN LOGOUT
# =====================================================

@admin.route("/admin-logout")
def admin_logout():

    session.pop("admin_id", None)
    session.pop("admin_name", None)
    session.pop("admin_email", None)

    flash(
        "Admin Logged Out Successfully!",
        "success"
    )

    return redirect("/admin-login")