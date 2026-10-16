from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    request,
    flash
)

from database.db import get_db_connection

import requests
import re
import os
from werkzeug.utils import secure_filename


materials = Blueprint("materials", __name__)


# =====================================================
# UPLOAD SETTINGS
# =====================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

UPLOAD_FOLDER_ABS = os.path.join(
    PROJECT_ROOT,
    "static",
    "study_materials"
)


def resolve_project_path(relative_path):
    """
    Database me stored relative path ko
    project root ke according absolute path me convert karta hai.
    """

    if not relative_path:
        return None

    normalized = relative_path.replace(
        "\\",
        os.sep
    ).replace(
        "/",
        os.sep
    )

    return os.path.join(
        PROJECT_ROOT,
        normalized
    )

ALLOWED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "ppt",
    "pptx",
    "txt"
}


def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =====================================================
# STUDY MATERIALS PAGE
# =====================================================

@materials.route("/materials")
def study_materials():

    # =========================
    # Login Check
    # =========================

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]


    # =========================
    # Online Search Query
    # =========================

    search_query = request.args.get(
        "online",
        ""
    ).strip()


    # =========================
    # Database
    # =========================

    connection = get_db_connection()
    cursor = connection.cursor()


    # =========================
    # Get User PDFs
    # =========================

    cursor.execute(
        """
        SELECT
            id,
            pdf_name,
            upload_date
        FROM pdfs
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    )

    pdfs = cursor.fetchall()


    # =========================
    # Get User Study Materials
    # =========================

    cursor.execute(
        """
        SELECT
            id,
            title,
            description,
            file_path,
            source_pdf_id,
            created_at
        FROM study_materials
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    )

    saved_materials = cursor.fetchall()


    # =========================
    # Study Material Count
    # =========================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM study_materials
        WHERE user_id = ?
        """,
        (user_id,)
    )

    material_count = cursor.fetchone()[0]


    connection.close()


    # =========================
    # Online Materials
    # =========================

    online_materials = []


    if search_query:

        try:

            response = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": search_query,
                    "format": "json",
                    "utf8": 1,
                    "srlimit": 8
                },
                headers={
                    "User-Agent":
                    "AI-Study-Assistant/1.0"
                },
                timeout=10
            )

            response.raise_for_status()

            result = response.json()

            search_results = (
                result
                .get("query", {})
                .get("search", [])
            )


            for item in search_results:

                title = item.get(
                    "title",
                    ""
                )

                snippet = item.get(
                    "snippet",
                    ""
                )


                description = re.sub(
                    r"<.*?>",
                    "",
                    snippet
                )


                url = (
                    "https://en.wikipedia.org/wiki/"
                    + title.replace(
                        " ",
                        "_"
                    )
                )


                online_materials.append({

                    "title": title,

                    "description":
                        description,

                    "url": url

                })


        except Exception as e:

            print(
                "ONLINE MATERIAL ERROR:"
            )

            print(repr(e))


    # =========================
    # Render
    # =========================

    return render_template(
        "study_material.html",

        pdfs=pdfs,

        saved_materials=saved_materials,

        material_count=material_count,

        online_materials=online_materials,

        online_query=search_query
    )


# =====================================================
# DIRECT ADD STUDY MATERIAL
# =====================================================

@materials.route(
    "/materials/add",
    methods=["POST"]
)
def add_study_material():

    # =========================
    # Login Check
    # =========================

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]


    # =========================
    # Get Form Data
    # =========================

    title = request.form.get(
        "title",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    file = request.files.get(
        "material_file"
    )


    # =========================
    # Validation
    # =========================

    if not title:

        flash(
            "Please enter a material title!",
            "danger"
        )

        return redirect("/materials")


    if not file or file.filename == "":

        flash(
            "Please choose a file!",
            "danger"
        )

        return redirect("/materials")


    if not allowed_file(file.filename):

        flash(
            "Invalid file type! Allowed: PDF, DOC, DOCX, PPT, PPTX and TXT.",
            "danger"
        )

        return redirect("/materials")


    # =========================
    # Create Folder
    # =========================

    os.makedirs(
        UPLOAD_FOLDER_ABS,
        exist_ok=True
    )


    # =========================
    # Secure Filename
    # =========================

    original_filename = secure_filename(
        file.filename
    )


    # =========================
    # Unique Filename
    # =========================

    import uuid

    unique_filename = (
        str(uuid.uuid4())
        + "_"
        + original_filename
    )


    # Relative path database me save hoga
    database_file_path = os.path.join(
        "static",
        "study_materials",
        unique_filename
    ).replace(
        "\\",
        "/"
    )

    # Absolute path file system par save karne ke liye
    absolute_file_path = os.path.join(
        UPLOAD_FOLDER_ABS,
        unique_filename
    )


    # =========================
    # Save File
    # =========================

    try:

        file.save(absolute_file_path)


        # =========================
        # Database
        # =========================

        connection = get_db_connection()
        cursor = connection.cursor()


        cursor.execute(
            """
            INSERT INTO study_materials(
                user_id,
                title,
                description,
                file_path,
                source_pdf_id
            )
            VALUES(?,?,?,?,?)
            """,
            (
                user_id,
                title,
                description,
                database_file_path,
                None
            )
        )


        connection.commit()

        connection.close()


        flash(
            "Study Material added successfully!",
            "success"
        )


    except Exception as e:

        print(
            "DIRECT MATERIAL UPLOAD ERROR:"
        )

        print(repr(e))


        # Remove file if database insertion failed

        if os.path.exists(absolute_file_path):

            try:
                os.remove(absolute_file_path)

            except OSError:
                pass


        flash(
            "Error adding Study Material!",
            "danger"
        )


    return redirect("/materials")


# =====================================================
# ADD EXISTING PDF TO STUDY MATERIALS
# =====================================================

@materials.route(
    "/materials/add-pdf/<int:pdf_id>",
    methods=["POST"]
)
def add_pdf_to_materials(pdf_id):

    # =========================
    # Login Check
    # =========================

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]


    connection = get_db_connection()
    cursor = connection.cursor()


    try:

        # =========================
        # Get User PDF
        # =========================

        cursor.execute(
            """
            SELECT
                id,
                pdf_name,
                file_path
            FROM pdfs
            WHERE id = ?
            AND user_id = ?
            """,
            (
                pdf_id,
                user_id
            )
        )

        pdf = cursor.fetchone()


        if not pdf:

            flash(
                "PDF not found!",
                "danger"
            )

            return redirect("/materials")


        pdf_id = pdf[0]
        pdf_name = pdf[1]
        file_path = pdf[2]


        # =========================
        # Duplicate Check
        # =========================

        cursor.execute(
            """
            SELECT id
            FROM study_materials
            WHERE user_id = ?
            AND source_pdf_id = ?
            """,
            (
                user_id,
                pdf_id
            )
        )

        already_added = cursor.fetchone()


        if already_added:

            flash(
                "This PDF is already in Study Materials!",
                "warning"
            )

            return redirect("/materials")


        # =========================
        # Add PDF
        # =========================

        cursor.execute(
            """
            INSERT INTO study_materials(
                user_id,
                title,
                description,
                file_path,
                source_pdf_id
            )
            VALUES(?,?,?,?,?)
            """,
            (
                user_id,
                pdf_name,
                "Added from your uploaded PDF.",
                file_path,
                pdf_id
            )
        )


        connection.commit()


        flash(
            "PDF added to Study Materials successfully!",
            "success"
        )


    except Exception as e:

        connection.rollback()

        print(
            "ADD PDF MATERIAL ERROR:"
        )

        print(repr(e))


        flash(
            f"Error adding Study Material: {e}",
            "danger"
        )


    finally:

        connection.close()


    return redirect("/materials")


# =====================================================
# DELETE STUDY MATERIAL
# =====================================================

@materials.route(
    "/materials/delete/<int:material_id>",
    methods=["POST"]
)
def delete_study_material(material_id):

    # =========================
    # Login Check
    # =========================

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]


    connection = get_db_connection()
    cursor = connection.cursor()


    try:

        # =========================
        # Get Material
        # =========================

        cursor.execute(
            """
            SELECT
                id,
                file_path,
                source_pdf_id
            FROM study_materials
            WHERE id = ?
            AND user_id = ?
            """,
            (
                material_id,
                user_id
            )
        )

        material = cursor.fetchone()


        if not material:

            flash(
                "Study Material not found!",
                "danger"
            )

            return redirect("/materials")


        file_path = material[1]
        source_pdf_id = material[2]


        # =================================================
        # Important:
        # If material came from uploaded PDF,
        # don't delete original PDF file.
        # =================================================

        if not source_pdf_id:

            absolute_file_path = (
                resolve_project_path(file_path)
            )

            if (
                absolute_file_path
                and os.path.isfile(absolute_file_path)
            ):

                try:

                    os.remove(absolute_file_path)

                except OSError:

                    pass


        # =========================
        # Delete Database Record
        # =========================

        cursor.execute(
            """
            DELETE FROM study_materials
            WHERE id = ?
            AND user_id = ?
            """,
            (
                material_id,
                user_id
            )
        )


        connection.commit()


        flash(
            "Study Material deleted successfully!",
            "success"
        )


    except Exception as e:

        connection.rollback()

        print(
            "DELETE MATERIAL ERROR:"
        )

        print(repr(e))


        flash(
            "Error deleting Study Material!",
            "danger"
        )


    finally:

        connection.close()


    return redirect("/materials")