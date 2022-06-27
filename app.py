from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)


login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "login"
login_manager.login_message_category = "info"

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()


def create_app():
    app = Flask(__name__)

    app.secret_key = "ea=n=K-t#LbH7[nvM']O`Gi4/C'>c="

    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://icedemfsxqcykk:8b3358b9f7efae126cbbb62448dc82b4d60cf5972849f3d3bdf61a8554bc9d75@ec2-54-155-61-133.eu-west-1.compute.amazonaws.com:5432/dcpi1dqrfvfni2"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

    login_manager.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    return app


app = create_app()
