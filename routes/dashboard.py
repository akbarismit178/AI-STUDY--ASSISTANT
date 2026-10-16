from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    request
)

from database.db import get_db_connection


dashboard = Blueprint("dashboard", __name__)


# =====================================================
# DASHBOARD
# =====================================================

@dashboard.route("/dashboard")
def dashboard_page():

    # =================================================
    # LOGIN CHECK
    # =================================================

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]


    # =================================================
    # SEARCH QUERY
    # =================================================

    search_query = request.args.get(
        "search",
        ""
    ).strip()


    # =================================================
    # DATABASE CONNECTION
    # =================================================

    connection = get_db_connection()
    cursor = connection.cursor()


    # =================================================
    # TOTAL USERS
    # =================================================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM users
        """
    )

    total_users = cursor.fetchone()[0]


    # =================================================
    # TOTAL PDFs
    # =================================================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM pdfs
        WHERE user_id = ?
        """,
        (user_id,)
    )

    total_pdfs = cursor.fetchone()[0]


    # =================================================
    # RECENT PDFs
    # =================================================

    cursor.execute(
        """
        SELECT
            id,
            pdf_name,
            upload_date,
            file_path
        FROM pdfs
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
        """,
        (user_id,)
    )

    pdfs = cursor.fetchall()


    # =================================================
    # TOTAL AI CHATS
    # =================================================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM chat_history
        WHERE user_id = ?
        """,
        (user_id,)
    )

    total_chats = cursor.fetchone()[0]


    # =================================================
    # TOTAL QUIZZES
    # =================================================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM quizzes
        WHERE user_id = ?
        """,
        (user_id,)
    )

    total_quizzes = cursor.fetchone()[0]


    # =================================================
    # TOTAL STUDY MATERIALS
    # =================================================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM study_materials
        WHERE user_id = ?
        """,
        (user_id,)
    )

    total_materials = cursor.fetchone()[0]


    # =================================================
    # PDF SEARCH
    # =================================================

    search_results = []


    if search_query:

        cursor.execute(
            """
            SELECT
                id,
                pdf_name,
                upload_date,
                file_path
            FROM pdfs
            WHERE user_id = ?
            AND pdf_name LIKE ?
            ORDER BY id DESC
            """,
            (
                user_id,
                f"%{search_query}%"
            )
        )

        rows = cursor.fetchall()


        # =================================================
        # CREATE SEARCH RESULT OBJECTS
        # =================================================

        for row in rows:

            search_results.append({

                "id": row[0],

                "title": row[1],

                "date": row[2],

                "file_path": row[3]

            })


    # =================================================
    # CLOSE DATABASE
    # =================================================

    connection.close()


    # =================================================
    # RENDER DASHBOARD
    # =================================================

    return render_template(

        "dashboard.html",

        total_users=total_users,

        total_pdfs=total_pdfs,

        total_chats=total_chats,

        total_quizzes=total_quizzes,

        total_materials=total_materials,

        pdfs=pdfs,

        search_query=search_query,

        search_results=search_results

    )