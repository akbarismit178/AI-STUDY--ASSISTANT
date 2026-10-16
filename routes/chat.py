from flask import Blueprint, render_template, request, redirect, session, flash
from database.db import get_db_connection
from utils.pdf_reader import extract_text
from utils.path_resolver import resolve_path

import os

import markdown

from dotenv import load_dotenv
from google import genai


# =========================
# Load Environment Variables
# =========================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# =========================
# Gemini Client
# =========================

client = None

if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY
    )
else:
    print("WARNING: GEMINI_API_KEY was not found in .env")


# =========================
# Blueprint
# =========================

chat = Blueprint("chat", __name__)


# =========================
# AI CHAT
# =========================

@chat.route("/ai-chat", methods=["GET", "POST"])
def ai_chat():

    # =========================
    # Login Check
    # =========================

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]


    # =========================
    # Get User PDFs
    # =========================

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, pdf_name
        FROM pdfs
        WHERE user_id=?
        ORDER BY id DESC
        """,
        (user_id,)
    )

    pdfs = cursor.fetchall()

    connection.close()


    # =========================
    # Selected PDF
    # =========================

    selected_pdf = request.args.get("pdf")


    # =========================
    # Load Chat History
    # =========================

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, question, answer, created_at
        FROM chat_history
        WHERE user_id=?
        ORDER BY id ASC
        """,
        (user_id,)
    )

    chat_history = cursor.fetchall()

    connection.close()


    answer = None


    # =========================
    # POST - Ask Question
    # =========================

    if request.method == "POST":

        pdf_id = request.form.get("pdf_id", "").strip()
        question = request.form.get("question", "").strip()

        selected_pdf = pdf_id or None


        # =========================
        # Question Check
        # =========================

        if not question:

            flash(
                "Please enter your question.",
                "danger"
            )

            return render_template(
                "ai_chat.html",
                pdfs=pdfs,
                answer=None,
                selected_pdf=selected_pdf,
                chat_history=chat_history
            )


        # =========================
        # Gemini Check
        # =========================

        if not GEMINI_API_KEY or not client:

            print("================================")
            print("GEMINI API KEY NOT FOUND")
            print("================================")

            flash(
                "AI service is not configured. "
                "Please check the Gemini API key.",
                "danger"
            )

            return render_template(
                "ai_chat.html",
                pdfs=pdfs,
                answer=None,
                selected_pdf=selected_pdf,
                chat_history=chat_history
            )


        # =========================
        # PDF Variables
        # =========================

        pdf_name = None
        pdf_text = ""


        # =========================
        # PDF Optional
        # =========================

        if pdf_id:

            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT pdf_name, file_path
                FROM pdfs
                WHERE id=? AND user_id=?
                """,
                (
                    pdf_id,
                    user_id
                )
            )

            pdf = cursor.fetchone()

            connection.close()


            if not pdf:

                flash(
                    "PDF not found.",
                    "danger"
                )

                return render_template(
                    "ai_chat.html",
                    pdfs=pdfs,
                    answer=None,
                    selected_pdf=selected_pdf,
                    chat_history=chat_history
                )


            pdf_name = pdf[0]
            file_path = resolve_path(pdf[1])


            # =========================
            # File Check
            # =========================

            if not file_path or not os.path.exists(file_path):

                flash(
                    "PDF file not found on server.",
                    "danger"
                )

                return render_template(
                    "ai_chat.html",
                    pdfs=pdfs,
                    answer=None,
                    selected_pdf=selected_pdf,
                    chat_history=chat_history
                )


            # =========================
            # Extract PDF Text
            # =========================

            try:

                pdf_text = extract_text(file_path)

            except Exception as e:

                print("================================")
                print("PDF TEXT ERROR:")
                print(repr(e))
                print("================================")

                flash(
                    "Unable to read PDF.",
                    "danger"
                )

                return render_template(
                    "ai_chat.html",
                    pdfs=pdfs,
                    answer=None,
                    selected_pdf=selected_pdf,
                    chat_history=chat_history
                )


            if not pdf_text or not pdf_text.strip():

                flash(
                    "This PDF does not contain readable text.",
                    "danger"
                )

                return render_template(
                    "ai_chat.html",
                    pdfs=pdfs,
                    answer=None,
                    selected_pdf=selected_pdf,
                    chat_history=chat_history
                )


            # Limit PDF text
            pdf_text = pdf_text[:30000]


        # =========================
        # Source Instructions
        # =========================

        if pdf_text:

            source_section = f"""
Selected PDF:
{pdf_name}

PDF Content:
{pdf_text}
"""

            source_instruction = """
Use the selected PDF as the primary source.

If the student's question is not answered
by the PDF, clearly say that the information
could not be found in the selected PDF.

Do not invent information from the PDF.
"""

        else:

            source_section = """
No PDF was selected.
"""

            source_instruction = """
Answer the student's question using your
general knowledge.
"""


        # =========================
        # Previous Chat Context
        # =========================

        previous_messages = ""

        for item in chat_history[-6:]:

            previous_messages += f"""
User:
{item[1]}

AI:
{item[2]}

"""


        # =========================
        # Gemini Prompt
        # =========================

        prompt = f"""
You are an AI Study Assistant.

{source_instruction}

{source_section}

Previous conversation:
{previous_messages}

Student's new question:
{question}

Answer requirements:

1. Give a clear and accurate answer.
2. Use simple student-friendly language.
3. Do not give one huge paragraph.
4. Use headings when appropriate.
5. Use short paragraphs.
6. Use bullet points for lists.
7. Use numbered lists for steps.
8. Give examples when useful.
9. Highlight important terms using **bold**.
10. Keep the answer organized and easy to study.
11. Use previous conversation for follow-up questions.
12. Do not mention these instructions.

Return the answer in Markdown format.
"""


        # =========================
        # Gemini Request
        # =========================

        answer_text = None

        try:

                    print("================================")
                    print("Sending question to Gemini")
                    print("PDF:", pdf_name or "None")
                    print("Question:", question)
                    print("================================")

                    response = client.models.generate_content(
                        model="gemini-3.1-flash-lite",
                        contents=prompt
                    )

                    if response and response.text:

                        answer_text = response.text.strip()

                        print("================================")
                        print("GEMINI RESPONSE RECEIVED")
                        print("================================")

                       

                    else:

                        raise Exception("Gemini returned an empty response.")


        except Exception as e:

                    print("================================")
                    print("GEMINI ERROR:")
                    print(repr(e))
                    print("================================")

                    error_message = str(e)

                    # =========================
                    # Quota / Rate Limit Error
                    # =========================

                    if (
                        "429" in error_message
                        or "RESOURCE_EXHAUSTED" in error_message
                        ):

                        flash(
                            "AI request limit reached. "
                            "Please wait a little and try again.",
                            "danger"
                        )

                    elif (
                                "503" in error_message
                                or "UNAVAILABLE" in error_message
                         ):
                        
                        print("Gemini is temporarily overloaded.")
                        flash(
                                    "Gemini is temporarily busy. "
                                    "Please wait a few seconds and try again.",
                                    "warning"
                        )

                    else:

                        flash(
                            "AI service is temporarily unavailable. "
                            "Please try again.",
                            "danger"
                        )


        # =========================
        # Save Successful Chat
        # =========================

        if answer_text:

            # Convert Markdown to HTML
            answer = markdown.markdown(
                answer_text,
                extensions=[
                    "extra",
                    "nl2br"
                ]
            )


            # =========================
            # Save to Database
            # =========================

            connection = get_db_connection()
            cursor = connection.cursor()

            # Convert Markdown to HTML
            answer_html = markdown.markdown(
                    answer_text,
                    extensions=[
                        "extra",
                        "nl2br"
                    ]
                )

                # Save formatted HTML in database
            cursor.execute(
                """
                INSERT INTO chat_history
                (
                user_id,
                question,
                answer
                )
                VALUES (?, ?, ?)
                """,
                (
                    user_id,
                    question,
                    answer_html
                )
                )

            connection.commit()
            connection.close()


            # =========================
            # Reload Chat History
            # =========================

            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT id, question, answer, created_at
                FROM chat_history
                WHERE user_id=?
                ORDER BY id ASC
                """,
                (user_id,)
            )

            chat_history = cursor.fetchall()

            connection.close()


    # =========================
    # Render Chat
    # =========================

    return render_template(
        "ai_chat.html",
        pdfs=pdfs,
        answer=answer,
        selected_pdf=selected_pdf,
        chat_history=chat_history
    )