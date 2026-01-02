import os
from flask import Flask
from dotenv import load_dotenv
from .db import db

def create_app():
    load_dotenv()

    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///logops.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["APP_VERSION"] = os.getenv("APP_VERSION", "0.1.0")

    db.init_app(app)

    with app.app_context():
        from . import models  # noqa: F401
        db.create_all()

    from .routes import bp
    app.register_blueprint(bp)

    return app
