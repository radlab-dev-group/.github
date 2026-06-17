from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path

db = SQLAlchemy()

# Resolve database path relative to this file's location
_WEB_APP_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _WEB_APP_DIR.parent.parent
INSTANCE_DIR = _PROJECT_ROOT / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)


class Example(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    original_id = db.Column(db.Integer)


class Annotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    example_id = db.Column(db.Integer, db.ForeignKey("example.id"), nullable=False)
    model_name = db.Column(db.String(255))
    model_label = db.Column(db.String(50))
    user_label = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, server_default=db.func.now())


def create_app(db_path=None):
    if db_path is None:
        db_path = f"sqlite:///{INSTANCE_DIR / 'data.db'}"

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app
