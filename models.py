from app import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pwd = db.Column(db.String(300), nullable=False, unique=True)

    def __repr__(self):
        return '<User %r>' % self.username


class Position(db.Model):
    __tablename__ = "HR Report"

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String())
    position = db.Column(db.String())
    year = db.Column(db.Integer())
    month = db.Column(db.Integer())
    ticket_id = db.Column(db.Integer(), unique=True, nullable=False)

    def __init__(self, source, position, year, month, ticket_id):
        self.source = source
        self.position = position
        self.year = year
        self.month = month
        self.ticket_id = ticket_id

    def __repr__(self):
        return f""


class Reviews(db.Model):
    __tablename__ = "Games Reviews"

    id = db.Column(db.Integer, primary_key=True)
    game_name = db.Column(db.String())
    review_source = db.Column(db.String())
    review_text = db.Column(db.String())
    stars = db.Column(db.String(7))
    ticket_id = db.Column(db.Integer(), unique=True, nullable=False)

    def __init__(self, game_name, review_source, review_text, stars, ticket_id):
        self.game_name = game_name
        self.review_source = review_source
        self.review_text = review_text
        self.stars = stars
        self.ticket_id = ticket_id

    def __repr__(self):
        return f""
