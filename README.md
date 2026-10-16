# AI Study Assistant

Flask-based AI Study Assistant that lets students upload PDFs, chat with an AI about their materials, generate quizzes, track progress, and manage study materials.

## Features

- User registration, login, logout, and session handling
- PDF upload, view, download, and delete
- AI chat powered by Google Gemini (with optional selected-PDF context)
- Quiz generation and history
- Study materials with online search (Wikipedia)
- Email notifications (welcome/login emails and contact form)
- Admin dashboard for managing users, PDFs, quizzes, chats, and materials
- Progress tracking dashboard

## Getting Started

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd AI_Study_Assistant_project
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example file and fill in your own values:

```bash
copy .env.example .env        # Windows
# or
cp .env.example .env          # macOS/Linux
```

**Important:** `.env` is already in `.gitignore` and must never be committed. Edit `.env` with your real credentials:

```env
# Gemini API key (AI chat & quiz)
GEMINI_API_KEY=your_gemini_api_key

# Gmail notification (contact form, welcome/login emails)
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_gmail_app_password
MAIL_RECEIVER=your_email@gmail.com

# Flask app
SECRET_KEY=your_random_long_secret_string
FLASK_DEBUG=0
HOST=0.0.0.0
PORT=5000

# Admin setup (run create_admin.py)
ADMIN_FULLNAME=Admin
ADMIN_EMAIL=your_admin_email@example.com
ADMIN_PASSWORD=your_strong_admin_password
```

Generate a strong `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(24))"
```

### 4. Initialize the database and create an admin

```bash
# Create the SQLite database and tables
python app.py

# In another terminal (or after stopping the app), create an admin account
python create_admin.py
```

`create_admin.py` reads `ADMIN_EMAIL` and `ADMIN_PASSWORD` from `.env`.

### 5. Run the application

```bash
python app.py
```

Then open http://localhost:5000

## Security

- `.env`, `venv/`, `__pycache__/`, `database/study.db`, `uploads/`, `static/study_materials/`, `instance/`, and IDE folders are excluded from git via `.gitignore`.
- Never commit `.env`. It contains API keys, mail passwords, and session secrets.
- All credentials are read from environment variables at runtime; none are hardcoded in source.
- If you previously committed a real API key, app password, or admin password, treat it as compromised: revoke and regenerate it, then update `.env`.

## Project Structure

```
app.py                      # Flask application factory and entry point
database/db.py              # SQLite schema and connection helpers
routes/                     # Blueprint route modules (auth, chat, quiz, upload, materials, dashboard, admin, home)
utils/                      # PDF text extraction and path resolution
static/                     # CSS, images, and publicly served study materials
templates/                  # Jinja2 HTML templates
uploads/                    # User-uploaded PDFs (excluded from git)
database/study.db           # Local SQLite database (excluded from git)
.env                        # Local secrets (excluded from git - never commit)
.env.example                # Committed placeholder template (safe to commit)
```

## License

MIT