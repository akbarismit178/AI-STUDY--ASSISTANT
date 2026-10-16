import os

from flask import Flask

from dotenv import load_dotenv

from database.db import create_database

from routes.home import home
from routes.auth import auth
from routes.dashboard import dashboard 
from routes.upload import upload
from routes.admin.admin import admin
from routes.chat import chat
from routes.materials import materials
from routes.quiz import quiz


load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "SECRET_KEY is not set. "
        "Configure it in .env (see .env.example)."
    )

# Database Create
create_database()

# Register Blueprints
app.register_blueprint(home)
app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(chat)
app.register_blueprint(upload)
app.register_blueprint(admin)
app.register_blueprint(materials)
app.register_blueprint(quiz)

if __name__ == "__main__":

    debug = os.getenv(
        "FLASK_DEBUG",
        "0"
    ) == "1"

    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 5000)),
        debug=debug
    )