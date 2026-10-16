import os
import sqlite3


DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "study.db"
)


# =========================
# Database Connection
# =========================

def get_db_connection():

    connection = sqlite3.connect(DATABASE)

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# =========================
# Create Database
# =========================

def create_database():

    connection = get_db_connection()

    cursor = connection.cursor()


    # =========================
    # Users
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        fullname TEXT NOT NULL,

        email TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL

    )
    """)


    # =========================
    # PDFs
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pdfs(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        pdf_name TEXT NOT NULL,

        file_path TEXT NOT NULL,

        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(user_id)
        REFERENCES users(id)

    )
    """)


    # =========================
    # Chat History
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        question TEXT NOT NULL,

        answer TEXT NOT NULL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(user_id)
        REFERENCES users(id)

    )
    """)


    # =========================
    # Quizzes
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quizzes(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        title TEXT NOT NULL,

        score INTEGER DEFAULT 0,

        total_questions INTEGER DEFAULT 0,

        correct_answers INTEGER DEFAULT 0,

        wrong_answers INTEGER DEFAULT 0,

        percentage REAL DEFAULT 0,

        question_data TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(user_id)
        REFERENCES users(id)

    )
    """)


    # =========================
    # Add Quiz History Columns
    # =========================

    quiz_columns = [

        ("total_questions", "INTEGER DEFAULT 0"),

        ("correct_answers", "INTEGER DEFAULT 0"),

        ("wrong_answers", "INTEGER DEFAULT 0"),

        ("percentage", "REAL DEFAULT 0"),

        ("question_data", "TEXT"),

        ("pdf_name", "TEXT")

    ]


    for column_name, column_type in quiz_columns:

        try:

            cursor.execute(
                f"""
                ALTER TABLE quizzes
                ADD COLUMN {column_name} {column_type}
                """
            )

        except sqlite3.OperationalError:

            # Column already exists
            pass


    # =========================
    # Study Materials
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS study_materials(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        title TEXT NOT NULL,

        description TEXT,

        file_path TEXT NOT NULL,

        source_pdf_id INTEGER,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(user_id)
        REFERENCES users(id),

        FOREIGN KEY(source_pdf_id)
        REFERENCES pdfs(id)

    )
    """)

    # =========================
    # Add Study Material Columns
    # =========================

    study_material_columns = [

        ("user_id", "INTEGER"),

        ("source_pdf_id", "INTEGER")

    ]


    for column_name, column_type in study_material_columns:

        try:

            cursor.execute(
                f"""
                ALTER TABLE study_materials
                ADD COLUMN {column_name} {column_type}
                """
            )

        except sqlite3.OperationalError:

            # Column already exists
            pass


    # =========================
    # Progress
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS progress(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        total_pdfs INTEGER DEFAULT 0,

        total_quizzes INTEGER DEFAULT 0,

        total_ai_chats INTEGER DEFAULT 0,

        FOREIGN KEY(user_id)
        REFERENCES users(id)

    )
    """)


    # =========================
    # Admins
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        fullname TEXT NOT NULL,

        email TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL

    )
    """)


    # =========================
    # Contact Messages
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contact_messages(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        email TEXT NOT NULL,

        subject TEXT NOT NULL,

        message TEXT NOT NULL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)


    # =========================
    # Save Database
    # =========================

    connection.commit()

    connection.close()