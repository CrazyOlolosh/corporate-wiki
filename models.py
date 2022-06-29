from app import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True, nullable=False)
    pwd = db.Column(db.String(300), nullable=False, unique=True)
    role = db.Column(db.String(30))
    user_pic = db.Column(db.String(120))
    confirmed = db.Column(db.Boolean, default=False)
    fav_spaces = db.Column(db.String())
    allowed_spaces = db.Column(db.String())
    fav_pages = db.Column(db.String())
    allowed_pages = db.Column(db.String())

    def __repr__(self):
        return '<User %r>' % self.username


class Page(db.Model):
    __tablename__ = "Pages"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(80))
    text = db.Column(db.String(), nullable=False)
    parent = db.Column(db.String(20))
    space = db.Column(db.String(30))
    limitations = db.Column(db.String(50))
    date = db.Column(db.Integer)

    def __init__(self, title, author, text, parent, space, limitations, date):
        self.title = title
        self.author = author
        self.text = text
        self.parent = parent
        self.space = space
        self.limitations = limitations
        self.date = date

    def __repr__(self):
        return f""


class Spaces(db.Model):
    __tablename__ = "Spaces"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String())
    homepage = db.Column(db.Integer)
    members = db.Column(db.Integer)
    parent = db.Column(db.String(20))
    limitations = db.Column(db.String(50))
    logo = db.Column(db.String())

    def __init__(self, name, description, homepage, members, parent, limitations, logo):
        self.name = name
        self.description = description
        self.homepage = homepage
        self.members = members
        self.parent = parent
        self.limitations = limitations
        self.logo = logo

    def __repr__(self):
        return f""