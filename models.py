from sqlalchemy import ForeignKey
from app import db
# from search import add_to_index, remove_from_index, query_index
from flask_login import UserMixin


# class SearchableMixin(object):
#     @classmethod
#     def search(cls, expression, page, per_page):
#         ids, total = query_index(cls.__tablename__, expression, page, per_page)
#         if total == 0:
#             return cls.query.filter_by(id=0), 0
#         when = []
#         for i in range(len(ids)):
#             when.append((ids[i], i))
#         return cls.query.filter(cls.id.in_(ids)).order_by(
#             db.case(when, value=cls.id)), total

#     @classmethod
#     def before_commit(cls, session):
#         session._changes = {
#             'add': list(session.new),
#             'update': list(session.dirty),
#             'delete': list(session.deleted)
#         }

#     @classmethod
#     def after_commit(cls, session):
#         for obj in session._changes['add']:
#             if isinstance(obj, SearchableMixin):
#                 add_to_index(obj.__tablename__, obj)
#         for obj in session._changes['update']:
#             if isinstance(obj, SearchableMixin):
#                 add_to_index(obj.__tablename__, obj)
#         for obj in session._changes['delete']:
#             if isinstance(obj, SearchableMixin):
#                 remove_from_index(obj.__tablename__, obj)
#         session._changes = None

#     @classmethod
#     def reindex(cls):
#         for obj in cls.query:
#             add_to_index(cls.__tablename__, obj)


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
    forbidden_pages = db.Column(db.String())
    last_online = db.Column(db.Integer, default=0)
    comm_rel = db.relationship("Comments", backref="c_author")
    ver_rel = db.relationship("Versions", backref="v_author")
    space_rel = db.relationship("Versions", backref="s_author")

    def __init__(self, username, name, email, pwd, role=None, user_pic=None, confirmed=False, fav_spaces=None, allowed_spaces=None, fav_pages=None, forbidden_pages=None, last_online=0):
        self.username = username
        self.name = name
        self.pwd = pwd
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.username


class Page(db.Model):
    __tablename__ = "Pages"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(80), ForeignKey('user.username'), nullable=False)
    text = db.Column(db.String(), nullable=False)
    parent = db.Column(db.Integer, ForeignKey('Pages.id'))
    space = db.Column(db.Integer, ForeignKey('Spaces.id'))
    limitations = db.Column(db.String(50))
    date = db.Column(db.Integer)
    children = db.relationship("Page")
    space_rel = db.relationship("Spaces", backref='space')
    user_rel = db.relationship("User", backref='user')
    version_rel = db.relationship("Versions", backref='origin_page')

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
    parent = db.Column(db.Integer)
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


class Versions(db.Model):
    __tablename__ = "Versions"

    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, ForeignKey('Pages.id'), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(120), nullable=False)
    text = db.Column(db.String(), nullable=False)
    author = db.Column(db.String(80), ForeignKey('user.username'), nullable=False)
    time = db.Column(db.Integer, nullable=False)
    page_rel = db.relationship("Page", backref='versions')


    def __init__(self, page_id, version, title, author, text, time):
        self.page_id = page_id
        self.version = version
        self.title = title
        self.text = text
        self.author = author
        self.time = time


    def __repr__(self):
        return f""


class Comments(db.Model):
    __tablename__ = "Comments"

    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, ForeignKey("Pages.id"), nullable=False)
    author = db.Column(db.Integer, ForeignKey("user.id"), nullable=False)
    text = db.Column(db.String(), nullable=False)
    time = db.Column(db.Integer, nullable=False)


    def __init__(self, page_id, author, text, time):
        self.page_id = page_id
        self.author = author
        self.text = text
        self.time = time
