from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from elasticsearch import Elasticsearch

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)
import os
from dotenv import load_dotenv

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "login"
login_manager.login_message_category = "info"

db = SQLAlchemy(session_options={'autocommit': True})
migrate = Migrate()
bcrypt = Bcrypt()


load_dotenv()
DATABASE_URI = os.environ.get("DATABASE_URI")
ELASTICSEARCH_URI = os.environ.get("ELASTICSEARCH_URI")


def create_app():
    app = Flask(__name__)

    app.secret_key = "ea=n=K-t#LbH7[nvM']O`Gi4/C'>c="

    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.elasticsearch = Elasticsearch(ELASTICSEARCH_URI)\
        if ELASTICSEARCH_URI else None

    login_manager.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    return app


app = create_app()
