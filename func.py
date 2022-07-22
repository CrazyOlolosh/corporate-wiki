from sqlalchemy import and_
from app import UPLOAD_FOLDER, SPACE_IMG_FOLDER, create_app, db, login_manager, bcrypt, mail, socketio
from models import Spaces, Tasks, User, Page, Versions, Comments


def task_get(id, **kwargs):
    task = Tasks.query.get(id)
    return task