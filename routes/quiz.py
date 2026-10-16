from flask import Blueprint, render_template, session, redirect, request, jsonify
from database.db import get_db_connection
from utils.pdf_reader import extract_text
from utils.path_resolver import resolve_path
import os
import json
from google import genai
import os
from dotenv import load_dotenv


# =========================
# Gemini Setup
# =========================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None

if GEMINI_API_KEY:

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

else:

    print(
        "WARNING: GEMINI_API_KEY was not found in .env"
    )


# =========================
# Blueprint
# =========================

quiz = Blueprint("quiz", __name__)

# =========================
# Quiz Page
# =========================

@quiz.route("/quiz")
def quiz_page():

    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, pdf_name
        FROM pdfs
        WHERE user_id=?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    )

    pdfs = cursor.fetchall()

    connection.close()

    selected_pdf = request.args.get("pdf")

    return render_template(
        "quiz.html",
        pdfs=pdfs,
        selected_pdf=selected_pdf
    )


# =========================
# Generate Quiz
# =========================

@quiz.route("/generate-quiz", methods=["POST"])
def generate_quiz():

    if "user_id" not in session:
        return jsonify({
            "error": "Please login first."
        }), 401


    data = request.get_json()

    title = data.get(
        "title",
        "AI Quiz"
        )

    score = data.get(
        "score",
        0
        )

    total_questions = data.get(
    "total_questions",
    0
)

    correct_answers = data.get(
        "correct_answers",
        score
        )

    wrong_answers = data.get(
        "wrong_answers",
        0
        )

    percentage = data.get(
        "percentage",
        0
        )

    question_data = data.get(
        "question_data",
        []
        )

    question_data = data.get(
    "question_data",
    []
)

    question_data_json = json.dumps(
        question_data,
        ensure_ascii=False
)
    if not data:
        return jsonify({
            "error": "Invalid request."
        }), 400


    pdf_id = data.get("pdf_id")
    question_count = data.get("count", 10)


    if not pdf_id:
        return jsonify({
            "error": "Please select a PDF."
        }), 400


    try:
        question_count = int(question_count)
    except (TypeError, ValueError):
        question_count = 10


    if question_count not in [5, 10, 15, 20]:
        question_count = 10


    # =========================
    # Get PDF
    # =========================

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
            session["user_id"]
        )
    )

    pdf = cursor.fetchone()

    connection.close()


    if not pdf:
        return jsonify({
            "error": "PDF not found."
        }), 404


    pdf_name = pdf[0]
    file_path = resolve_path(pdf[1])


    # =========================
    # Check File
    # =========================

    if not file_path or not os.path.exists(file_path):
        return jsonify({
            "error": "PDF file not found."
        }), 404


    # =========================
    # Extract PDF Text
    # =========================

    try:

        text = extract_text(file_path)

    except Exception as e:

        print("PDF EXTRACTION ERROR:")
        print(repr(e))

        return jsonify({
            "error": "Unable to read the PDF."
        }), 500


    if not text or not text.strip():

        return jsonify({
            "error": "This PDF does not contain readable text."
        }), 400


    # =========================
    # Limit Text Size
    # =========================

    text = text.strip()

    max_text_length = 30000

    if len(text) > max_text_length:
        text = text[:max_text_length]


    # =========================
    # Gemini Prompt
    # =========================

    prompt = f"""
You are an AI quiz generator for a study assistant.

Create exactly {question_count} multiple-choice questions
from the PDF content provided below.

Rules:

1. Questions must be based ONLY on the PDF content.
2. Each question must have exactly 4 options.
3. Only one option must be correct.
4. Keep questions clear and suitable for students.
5. Do not add information that is not present in the PDF.
6. Return ONLY valid JSON.
7. Do not use Markdown.
8. Do not add ```json or ``` around the response.

Required JSON format:

[
    {{
        "question": "Question text",
        "options": [
            "Option A",
            "Option B",
            "Option C",
            "Option D"
        ],
        "answer": 0
    }}
]

The "answer" value must be the zero-based index
of the correct option.

PDF Name:
{pdf_name}

PDF Content:
{text}
"""


    # =========================
    # Gemini Request
    # =========================

    try:

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt
        )


        if not response or not response.text:

            return jsonify({
                "error": "Gemini returned an empty response."
            }), 503


        raw_response = response.text.strip()


        # Remove accidental Markdown fences
        if raw_response.startswith("```"):

            raw_response = (
                raw_response
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )


        questions = json.loads(raw_response)


        if not isinstance(questions, list):

            raise ValueError(
                "Invalid quiz format."
            )


        # =========================
        # Validate Questions
        # =========================

        valid_questions = []


        for item in questions:

            if not isinstance(item, dict):
                continue


            question_text = item.get(
                "question"
            )

            options = item.get(
                "options"
            )

            answer = item.get(
                "answer"
            )


            if not question_text:
                continue


            if (
                not isinstance(options, list)
                or len(options) != 4
            ):
                continue


            if not isinstance(answer, int):
                continue


            if answer < 0 or answer > 3:
                continue


            valid_questions.append({

                "question":
                    str(question_text),

                "options": [
                    str(option)
                    for option in options
                ],

                "answer":
                    answer

            })


        if not valid_questions:

            return jsonify({
                "error":
                    "Gemini could not create a valid quiz."
            }), 503


        return jsonify({
            "questions": valid_questions
        })


    except json.JSONDecodeError as e:

        print("QUIZ JSON ERROR:")
        print(repr(e))

        return jsonify({
            "error":
                "AI returned an invalid quiz format."
        }), 503


    except Exception as e:

        print("QUIZ GENERATION ERROR:")
        print(repr(e))

        error_message = str(e)


        if (
            "429" in error_message
            or
            "RESOURCE_EXHAUSTED" in error_message
        ):

            return jsonify({
                "error":
                    "AI request limit reached. "
                    "Please wait and try again."
            }), 429


        if "503" in error_message:

            return jsonify({
                "error":
                    "AI service is temporarily busy. "
                    "Please try again in a moment."
            }), 503


        return jsonify({
            "error":
                "Unable to generate quiz right now."
        }), 500









# =========================
# Save Quiz Result
# =========================
@quiz.route("/save-quiz", methods=["POST"])
def save_quiz():

    if "user_id" not in session:
        return jsonify({
            "error": "Please login first."
        }), 401


    data = request.get_json()


    if not data:
        return jsonify({
            "error": "Invalid request."
        }), 400


    # =========================
    # Quiz Result Data
    # =========================

    title = data.get(
        "title",
        "AI Quiz"
    )

    score = data.get(
        "score",
        0
    )

    total_questions = data.get(
        "total_questions",
        0
    )

    correct_answers = data.get(
        "correct_answers",
        score
    )

    wrong_answers = data.get(
        "wrong_answers",
        0
    )

    percentage = data.get(
        "percentage",
        0
    )

    question_data = data.get(
        "question_data",
        []
    )


    # =========================
    # Convert Values
    # =========================

    try:
        score = int(score)

    except (TypeError, ValueError):
        score = 0


    try:
        total_questions = int(
            total_questions
        )

    except (TypeError, ValueError):
        total_questions = 0


    try:
        correct_answers = int(
            correct_answers
        )

    except (TypeError, ValueError):
        correct_answers = score


    try:
        wrong_answers = int(
            wrong_answers
        )

    except (TypeError, ValueError):
        wrong_answers = (
            total_questions -
            correct_answers
        )


    try:
        percentage = float(
            percentage
        )

    except (TypeError, ValueError):
        percentage = 0


    # =========================
    # Convert Questions
    # To JSON
    # =========================

    question_data_json = json.dumps(
        question_data
    )


    # =========================
    # Database
    # =========================

    connection = get_db_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        INSERT INTO quizzes(
            user_id,
            title,
            score,
            total_questions,
            correct_answers,
            wrong_answers,
            percentage,
            question_data
        )
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            session["user_id"],
            title,
            score,
            total_questions,
            correct_answers,
            wrong_answers,
            percentage,
            question_data_json
        )
    )


    connection.commit()

    connection.close()


    return jsonify({
        "success": True
    })



# =========================
# Quiz History
# =========================


@quiz.route("/quiz-history")
def quiz_history():

    if "user_id" not in session:
        return redirect("/login")


    connection = get_db_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            id,
            title,
            score,
            created_at,
            total_questions,
            correct_answers,
            wrong_answers,
            percentage,
            question_data
        FROM quizzes
        WHERE user_id=?
        ORDER BY id DESC
        """,
        (
            session["user_id"],
        )
    )


    quiz_rows = cursor.fetchall()


    connection.close()


    quizzes = []


    for row in quiz_rows:

        question_data = []


        if row[8]:

            try:

                question_data = json.loads(
                    row[8]
                )

            except (
                json.JSONDecodeError,
                TypeError
            ):

                question_data = []


        quizzes.append({

            "id": row[0],

            "title": row[1],

            "score": row[2],

            "created_at": row[3],

            "total_questions": row[4],

            "correct_answers": row[5],

            "wrong_answers": row[6],

            "percentage": row[7],

            "questions": question_data

        })


    return render_template(
        "quiz_history.html",
        quizzes=quizzes
    )


