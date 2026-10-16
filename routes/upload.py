from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    flash,
    send_file,
    current_app
)

from werkzeug.utils import secure_filename
from database.db import get_db_connection
from utils.pdf_reader import extract_text
from utils.path_resolver import resolve_path

import os


upload = Blueprint("upload", __name__)


# =====================================================
# UPLOAD FOLDER
# =====================================================

UPLOAD_FOLDER = "uploads"


def get_upload_path(file_path):
    """
    Database me stored file path ko
    proper absolute filesystem path me convert karta hai.
    """

    return resolve_path(file_path)


# =====================================================
# UPLOAD PDF
# =====================================================

@upload.route("/upload-pdf", methods=["GET", "POST"])
def upload_pdf():

    # Login Check
    if "user_id" not in session:
        return redirect("/login")


    # =================================================
    # POST - UPLOAD PDF
    # =================================================

    if request.method == "POST":

        pdf = request.files.get("pdf")


        # No PDF selected
        if pdf is None or pdf.filename == "":

            flash(
                "Please select a PDF.",
                "danger"
            )

            return redirect("/upload-pdf")


        # =================================================
        # File Validation
        # =================================================

        original_filename = pdf.filename

        if not original_filename.lower().endswith(".pdf"):

            flash(
                "Only PDF files are allowed.",
                "danger"
            )

            return redirect("/upload-pdf")


        filename = secure_filename(
            original_filename
        )


        if not filename:

            flash(
                "Invalid PDF filename.",
                "danger"
            )

            return redirect("/upload-pdf")


        # =================================================
        # Create Upload Folder
        # =================================================

        upload_folder_path = os.path.join(
            current_app.root_path,
            UPLOAD_FOLDER
        )

        os.makedirs(
            upload_folder_path,
            exist_ok=True
        )


        # =================================================
        # File Path
        # =================================================

        filepath = os.path.join(
            upload_folder_path,
            filename
        )


        # =================================================
        # Save PDF
        # =================================================

        pdf.save(filepath)


        # =================================================
        # Extract PDF Text
        # =================================================

        try:

            text = extract_text(filepath)

            print(
                "PDF TEXT PREVIEW:"
            )

            print(
                text[:500]
            )

        except Exception as e:

            print(
                "PDF TEXT EXTRACTION ERROR:"
            )

            print(
                repr(e)
            )


        # =================================================
        # Database
        # =================================================

        connection = get_db_connection()
        cursor = connection.cursor()


        # Database me relative path save karenge
        database_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        # Windows backslash ko slash me convert
        database_path = database_path.replace(
            "\\",
            "/"
        )


        cursor.execute(
            """
            INSERT INTO pdfs
            (
                user_id,
                pdf_name,
                file_path
            )
            VALUES (?, ?, ?)
            """,
            (
                session["user_id"],
                filename,
                database_path
            )
        )


        connection.commit()
        connection.close()


        flash(
            "PDF Uploaded Successfully!",
            "success"
        )


        return redirect(
            "/upload-pdf"
        )


    # =================================================
    # GET - SHOW PDFs
    # =================================================

    connection = get_db_connection()
    cursor = connection.cursor()


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
        """,
        (
            session["user_id"],
        )
    )


    pdfs = cursor.fetchall()

    connection.close()


    return render_template(
        "upload_pdf.html",
        pdfs=pdfs
    )


# =====================================================
# VIEW PDF
# =====================================================

@upload.route(
    "/view-pdf/<int:pdf_id>"
)
def view_pdf(pdf_id):

    # Login Check
    if "user_id" not in session:
        return redirect("/login")


    connection = get_db_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            pdf_name,
            file_path
        FROM pdfs
        WHERE id = ?
        AND user_id = ?
        """,
        (
            pdf_id,
            session["user_id"]
        )
    )


    pdf = cursor.fetchone()

    connection.close()


    # PDF database me nahi mila
    if not pdf:

        flash(
            "PDF Not Found!",
            "danger"
        )

        return redirect(
            "/upload-pdf"
        )


    pdf_name = pdf[0]
    database_path = pdf[1]


    # =================================================
    # Resolve Actual File Path
    # =================================================

    filepath = get_upload_path(
        database_path
    )


    # =================================================
    # Check File Exists
    # =================================================

    if not filepath or not os.path.isfile(filepath):

        print(
            "PDF FILE NOT FOUND:"
        )

        print(
            filepath
        )

        flash(
            "PDF file is missing from the server.",
            "danger"
        )

        return redirect(
            "/upload-pdf"
        )


    # =================================================
    # Open PDF in Browser
    # =================================================

    return send_file(
        filepath,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=pdf_name
    )


# =====================================================
# DOWNLOAD PDF
# =====================================================

@upload.route(
    "/download-pdf/<int:pdf_id>"
)
def download_pdf(pdf_id):

    # Login Check
    if "user_id" not in session:
        return redirect("/login")


    connection = get_db_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            pdf_name,
            file_path
        FROM pdfs
        WHERE id = ?
        AND user_id = ?
        """,
        (
            pdf_id,
            session["user_id"]
        )
    )


    pdf = cursor.fetchone()

    connection.close()


    if not pdf:

        flash(
            "PDF Not Found!",
            "danger"
        )

        return redirect(
            "/upload-pdf"
        )


    pdf_name = pdf[0]
    database_path = pdf[1]


    filepath = get_upload_path(
        database_path
    )


    if not filepath or not os.path.isfile(filepath):

        flash(
            "PDF file is missing from the server.",
            "danger"
        )

        return redirect(
            "/upload-pdf"
        )


    return send_file(
        filepath,
        as_attachment=True,
        download_name=pdf_name,
        mimetype="application/pdf"
    )


# =====================================================
# DELETE PDF
# =====================================================

@upload.route(
    "/delete-pdf/<int:pdf_id>",
    methods=["POST", "GET"]
)
def delete_pdf(pdf_id):

    # Login Check
    if "user_id" not in session:
        return redirect("/login")


    connection = get_db_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            file_path
        FROM pdfs
        WHERE id = ?
        AND user_id = ?
        """,
        (
            pdf_id,
            session["user_id"]
        )
    )


    pdf = cursor.fetchone()


    if not pdf:

        connection.close()

        flash(
            "PDF Not Found!",
            "danger"
        )

        return redirect(
            "/upload-pdf"
        )


    database_path = pdf[0]

    filepath = get_upload_path(
        database_path
    )


    # =================================================
    # Delete Physical File
    # =================================================

    if filepath and os.path.isfile(filepath):

        try:

            os.remove(filepath)

        except Exception as e:

            print(
                "PDF DELETE FILE ERROR:"
            )

            print(
                repr(e)
            )


    # =================================================
    # Delete Database Record
    # =================================================

    cursor.execute(
        """
        DELETE FROM pdfs
        WHERE id = ?
        AND user_id = ?
        """,
        (
            pdf_id,
            session["user_id"]
        )
    )


    connection.commit()
    connection.close()


    flash(
        "PDF Deleted Successfully!",
        "success"
    )


    return redirect(
        "/upload-pdf"
    )