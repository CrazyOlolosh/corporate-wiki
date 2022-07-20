from flask import (
    Flask,
    render_template,
    redirect,
    flash,
    url_for,
    session,
    send_from_directory,
    request,
    Response,
    jsonify,
    g,
)

from datetime import datetime, timedelta
import time
from sqlalchemy import desc, and_, not_, or_
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import (
    IntegrityError,
    DataError,
    DatabaseError,
    InterfaceError,
    InvalidRequestError,
)
from werkzeug.routing import BuildError
from werkzeug.utils import secure_filename


from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)

from flask_mail import Message

from app import UPLOAD_FOLDER, SPACE_IMG_FOLDER, create_app, db, login_manager, bcrypt, mail, socketio
from models import Spaces, Tasks, User, Page, Versions, Comments
from forms import comment_form, login_form, register_form, post_form, permission_form, space_form


import random
import string
import threading
from json import dumps, loads
import re
import requests
from httplib2 import Http
from bs4 import BeautifulSoup
from flask_cors import CORS
import os
import sys


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app = create_app()
CORS(app)


@app.before_request
def session_handler():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=720)


@socketio.on('connected')
def custom_connect_event(json, methods=['GET', 'POST']):
    db.session.begin()
    current_user.online = True
    print(f"{current_user.username} is online. {current_user.online}")
    db.session.commit()
    db.session.close()


@socketio.on('disconnected')
def custom_disconnect_event(json, methods=['GET', 'POST']):
    date = int(time.time())
    db.session.begin()
    username = json['user']
    user = User.query.filter(User.username == username).first()
    user.last_online = date
    user.online = False
    print(f"{user.username} is offline. {user.online}")
    db.session.commit()
    db.session.close()


@app.route("/", methods=("GET", "POST"), strict_slashes=False)
def index():
    if current_user.is_authenticated:
        try:
            request.args['space']
        except KeyError:
            parent = None
        else:
            parent = request.args['space']

        if current_user.fav_spaces:
            fav_list = current_user.fav_spaces[1:-1].split(",")
        else:
            fav_list = []
        if current_user.allowed_spaces:
            s_list = current_user.allowed_spaces[1:-1].split(",")
            spaces_raw = Spaces.query.filter(and_(Spaces.parent == parent, Spaces.id.in_(s_list))).order_by(desc(Spaces.id.in_(fav_list))).all()
        else:
            if current_user.role == "Admin":
                spaces_raw = Spaces.query.filter(Spaces.parent == parent).order_by(desc(Spaces.id.in_(fav_list))).all()
            else:
                spaces_raw = []

        if len(spaces_raw) < 1:
            p = Spaces.query.get(parent)
            try:
                homepage_id = p.homepage
            except AttributeError:
                return render_template('ftu.html')
            else:    
                return redirect(url_for('page', id=homepage_id))

        spaces = [
            {
                "id": space.id,
                "parrent": space.parent,
                "name": space.name,
                "image": space.logo,
                "members": space.members,
                "description": space.description,
                "homepage": space.homepage,
            }
            for space in spaces_raw
        ]
        
        fav_list = dumps(fav_list)
    else:
        spaces = []
        fav_list = []

    return render_template("index.html", title="Главная", spaces=spaces, action="main", fav=fav_list, origin='fillin')


# @app.route("/fetch/<space>", methods=("GET", "POST"))
# @login_required
# def space_fetch(p_space):
#     s_list = [
#         {
#             'id': space.id,
#             'homepage': space.homepage,
#             'image': space.logo,
#             'members': space.members,
#             'name': space.name
#         } for space in Spaces.query.filter(Spaces.parent == p_space.id)
#     ]
#     return


@app.route("/login", methods=("GET", "POST"), strict_slashes=False)
def login():
    form = login_form()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            if check_password_hash(user.pwd, form.pwd.data):
                login_user(user)
                return redirect(url_for("index"))
            else:
                flash("Invalid Username or password!", "error")
        except Exception as e:
            flash(e, "error")

    return render_template(
        "auth.html", form=form, text="Login", title="Login", btn_action="Login"
    )


# Register route
@app.route("/register", methods=("GET", "POST"), strict_slashes=False)
def register():
    form = register_form()
    if form.validate_on_submit():
        try:
            email = form.email.data
            pwd = form.pwd.data
            name = form.name.data
            username = str(email).split("@")[0]
            db.session.begin()
            newuser = User(
                username=username,
                name=name,
                email=email,
                pwd=bcrypt.generate_password_hash(pwd).decode("utf-8"),
            )

            db.session.add(newuser)
            db.session.commit()
            db.session.close()
            flash(f"Account Succesfully created", "success")
            return redirect(url_for("login"))

        except InvalidRequestError:
            db.session.rollback()
            flash(f"Something went wrong!", "error")
        except IntegrityError:
            db.session.rollback()
            flash(f"User already exists!.", "warning")
        except DataError:
            db.session.rollback()
            flash(f"Invalid Entry", "warning")
        except InterfaceError:
            db.session.rollback()
            flash(f"Error connecting to the database", "error")
        except DatabaseError:
            db.session.rollback()
            flash(f"Error connecting to the database", "error")
        except BuildError:
            db.session.rollback()
            flash(f"An error occured !", "error")
    return render_template(
        "auth.html",
        form=form,
        text="Create account",
        title="Register",
        btn_action="Register account",
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template("404.html"), 404


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


# SECURE_FILENAME CYRILYC FIX
text_type = str

_windows_device_files = (
    "CON",
    "AUX",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "LPT1",
    "LPT2",
    "LPT3",
    "PRN",
    "NUL",
)

_filename_strip_re = re.compile(r"[^A-Za-zа-яА-ЯёЁ0-9_.-]")


def secure_filename(filename: str) -> str:
    if isinstance(filename, text_type):
        from unicodedata import normalize

        filename = normalize("NFKD", filename)

    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, " ")

    filename = str(_filename_strip_re.sub("", "_".join(filename.split()))).strip("._")

    if (
        os.name == "nt"
        and filename
        and filename.split(".")[0].upper() in _windows_device_files
    ):
        filename = f"_{filename}"

    return filename


# END


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {"txt", "pdf", "docx", "xlsx", "jpg", "png", 'gif', 'svg'}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            pre_path = os.path.join(app.config["UPLOAD_FOLDER"])
            path = uniquify(f"{pre_path}/{filename}")
            filename = path.split("/")[-1]
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            return f"READY:{UPLOAD_FOLDER}/{filename}"


def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 1

    while os.path.exists(path):
        path = filename + " (" + str(counter) + ")" + extension
        counter += 1

    return path


@app.route("/upload/<name>")
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


@app.route("/create", methods=("GET", "POST"), strict_slashes=False)
@login_required
def post():
    ref = request.referrer.split("/")[-1]
    if "page?id=" in ref:
        ref_id = ref.split("id=")[-1]
        ref_page = Page.query.get(ref_id)
        space_default = ref_page.space
        parent_default = ref_page.parent
        form = post_form(space=space_default, parent=parent_default)
        if current_user.forbidden_pages != "{}":
            p_list = current_user.forbidden_pages[1:-1].split(",")
            parent_choices = [
                (page.id, page.title)
                for page in Page.query.filter(
                    and_(Page.space == space_default, not_(Page.id.in_(p_list)))
                )
                .order_by(Page.parent, Page.id)
                .all()
            ]
        else:
            parent_choices = [
                (page.id, page.title)
                for page in Page.query.filter(Page.space == space_default)
                .order_by(Page.parent, Page.id)
                .all()
            ]
        parent_choices.insert(0, (None, "Без родителя"))
        form.parent.choices = parent_choices
    else:
        form = post_form()

    if current_user.allowed_spaces:
        s_list = current_user.allowed_spaces[1:-1].split(",")
        form.space.choices = [
            (space.id, space.name)
            for space in Spaces.query.filter(Spaces.id.in_(s_list))
            .order_by(Spaces.parent, Spaces.id)
            .all()
        ]
    else:
        form.space.choices = [
            (space.id, space.name)
            for space in Spaces.query.order_by(Spaces.parent, Spaces.id).all()
        ]

    if form.is_submitted():
        text = form.post.data
        text = text.replace("\n", "")
        text = text.replace("\\n", "")
        if "\n" in text:
            print("Catch newline!")
        title = form.heading.data
        print(form.parent.data)
        if form.parent.data == "None" or form.parent.data == "":
            parent = None
        else:
            parent = form.parent.data
        print(type(parent))
        space = form.space.data
        limitations = ""

        date = int(time.time())
        db.session.begin()
        new_page = Page(
            title=title,
            author=current_user.username,
            text=text,
            date=date,
            parent=parent,
            space=space,
            limitations=limitations,
        )

        db.session.add(new_page)
        db.session.commit()

        db.session.begin()
        page = (
            Page.query.filter(Page.author == current_user.username)
            .order_by(desc(Page.date))
            .first()
        )
        page_id = page.id
        post_text_soup = BeautifulSoup(text, "html.parser")
        post_text = post_text_soup.text
        post = {
            "title": title,
            "text": post_text,
        }
        es_resp = app.elasticsearch.index(index="posts", id=page_id, body=post)
        print(es_resp)
        db.session.commit()
        db.session.close()

        return redirect(url_for("page", id=page_id))

    return render_template(
        "create.html", action="create", form=form, title="Новая запись"
    )


def page_fetch_child(child_id):
    c_list = []

    def recursion(id):
        if Page.query.filter(Page.parent == id).all():
            for child in Page.query.filter(Page.parent == id).all():
                c_list.append(child)
                recursion(child.id)
        return c_list
    recursion(child_id)
    
    return c_list


@app.route("/edit", methods=("GET", "POST"), strict_slashes=False)
@login_required
def edit():
    if request.method == "GET":
        try:
            id = request.args["id"]
        except KeyError:
            return render_template(url_for("page_not_found"))

    if request.method == "POST":
        ref = request.referrer.split("/")[-1]
        if "?id=" in ref:
            id = ref.split("id=")[-1]

    page = Page.query.get(id)
    form = post_form(space=page.space, parent=page.parent)
    form.heading.data = page.title
    parent_choices = [
        (page_r.id, page_r.title)
        for page_r in Page.query.filter(Page.space == page.space)
        .order_by(Page.parent, Page.id)
        .all()
    ]
    parent_choices.insert(0, (None, "Без родителя"))
    form.parent.choices = parent_choices

    if current_user.allowed_spaces:
        s_list = current_user.allowed_spaces[1:-1].split(",")
        form.space.choices = [
            (space.id, space.name)
            for space in Spaces.query.filter(Spaces.id.in_(s_list))
            .order_by(Spaces.parent, Spaces.id)
            .all()
        ]
    else:
        form.space.choices = [
            (space.id, space.name)
            for space in Spaces.query.order_by(Spaces.parent, Spaces.id).all()
        ]

    page_text = page.text
    page_text = page_text.replace('\\', '\\\\')
    page_text = page_text.replace('"', '\\"')
    page_text = page_text.replace("\n", "")
    if "\n" in page_text:
        print("!Catch!")
    page_title = page.title

    versions_list = [
        {
            "id": version.id,
            "version": version.version,
            "author": version.v_author.name,
            "time": datetime.fromtimestamp(int(version.time)).strftime(
                "%Y-%m-%d %H:%M"
            ),
        }
        for version in Versions.query.filter(Versions.page_id == id)
        .order_by(Versions.version)
        .all()
    ]

    if form.is_submitted():
        text = form.post.data
        text = text.replace("\n", "")
        text = text.replace("\\n", "")
        if "\n" in text:
            print("!Catch!")
        title = form.heading.data
        parent = form.parent.data
        if parent == "None" or parent == "":
            parent = None
        space = form.space.data
        limitations = ""

        date = int(time.time())
        db.session.begin()
        ver_num = len(Versions.query.filter(Versions.page_id == page.id).all())
        new_backup = Versions(
            page_id=page.id,
            version=ver_num + 1,
            title=page.title,
            text=page.text.replace("\n", ""),
            author=current_user.username,
            time=date,
        )

        print(page.p_author.email)
        msg = Message(
            subject=f"Изменение страницы {page.title}",
            recipients=[page.p_author.email],
            body="В созданной вами станице произошли изменения",
            sender="notify@kindofconfluence.com",
        )



        page.title = title
        page.text = text
        if page.space == space:
            page.space = space
        else:
            child_list = page_fetch_child(page.id)
            print(child_list)
            for child in child_list:
                child.space = space
            page.space = space
        page.parent = parent

        db.session.add(new_backup)

        post_text_soup = BeautifulSoup(text, "html.parser")
        post_text = post_text_soup.text
        post = {
            "title": title,
            "text": post_text,
        }
        es_resp = app.elasticsearch.index(index="posts", id=page.id, body=post)
        print(es_resp)
        db.session.commit()
        db.session.close()

        # mail.send(msg)  # Unable from localhost

        return redirect(url_for("page", id=id))

    return render_template(
        "create.html",
        action="edit",
        form=form,
        title="Редактирование",
        text=page_text,
        p_title=page_title,
        versions=versions_list,
    )


@app.route("/preview", methods=("GET", "POST"), strict_slashes=False)
@login_required
def preview():
    pre_id = request.args["id"]
    version = Versions.query.get(pre_id)
    title = version.title
    pid = version.page_id
    text = version.text
    return render_template(
        "preview.html", id=pid, title=title, text=text, action="preview"
    )


@app.route("/restore", methods=("GET", "POST"), strict_slashes=False)
@login_required
def restore():
    if "edit?id=" in request.referrer:
        pre_id = request.args["id"]
        db.session.begin()
        
        # Update current page from version and remove newer
        version = Versions.query.get(pre_id)
        id = version.page_id
        page = Page.query.get(id)
        
        page.text = version.text
        page.title = version.title

        remove_versions = Versions.query.filter(
            and_(
                Versions.version > version.version, Versions.page_id == id
            )
        )
        for version in remove_versions:
            db.session.delete(version)

        db.session.commit()
        db.session.close()

        return redirect(url_for("page", id=id))
    else:
        return render_template(url_for("index"))


@app.route("/page", methods=("GET", "POST"))
@login_required
def page():

    comment = comment_form()
    if request.method == "GET":
        try:
            id = request.args["id"]
        except KeyError:
            return render_template("404.html")

        if id == "None":
            return render_template("404.html")

        try:
            page_note = Page.query.get(id)
            title = page_note.title
            text = page_note.text
            space = page_note.space
        except AttributeError:
            return render_template("404.html")

        comments_list = [
            {
                "text": comment.text,
                "author": comment.c_author.name,
                "author_img": comment.c_author.user_pic,
                "author_active": comment.c_author.online,
                "time": datetime.fromtimestamp(int(comment.time)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
            }
            for comment in Comments.query.filter(Comments.page_id == id)
            .order_by(Comments.time)
            .all()
        ]

        return render_template(
            "page.html",
            id=id,
            title=title,
            text=text,
            space=space,
            comment=comment,
            comments=comments_list,
            action="page",
        )

    if comment.is_submitted():
        ref = request.referrer.split("/")[-1]
        if "page?id=" in ref:
            id = ref.split("id=")[-1]
        date = int(time.time())
        com_text = comment.text.data
        page_id = id
        author = current_user.id
        c_time = date

        db.session.begin()
        new_comment = Comments(
            page_id=page_id, author=author, text=com_text, time=c_time
        )
        db.session.add(new_comment)
        db.session.commit()
        db.session.close()

        return redirect(url_for("page", id=id))


@app.route("/spaces", methods=("GET", "POST"))
@login_required
def spaces():
    if request.method == "GET":
        if current_user.fav_spaces:
            fav_list = current_user.fav_spaces[1:-1].split(",")
        else:
            fav_list = []
        if current_user.allowed_spaces:
            s_list = current_user.allowed_spaces[1:-1].split(",")
            spaces_raw = Spaces.query.filter(Spaces.id.in_(s_list)).order_by(desc(Spaces.id.in_(fav_list))).all()
        else:
            spaces_raw = Spaces.query.order_by(desc(Spaces.id.in_(fav_list))).all()

        spaces = [
            {
                "id": space.id,
                "parrent": space.parent,
                "name": space.name,
                "image": space.logo,
                "members": space.members,
                "description": space.description,
                "homepage": space.homepage,
            }
            for space in spaces_raw
        ]

        return render_template(
            "spaces.html", title="Пространства", spaces=spaces, action="space", fav=fav_list
        )


@app.route("/space", methods=("GET", "POST"))
@login_required
def space():
    if current_user.role == 'Admin':
        sid = request.args['id']
        space = Spaces.query.get(sid)

        title = space.name
        description = space.description
        logo = space.logo
        form = space_form(homepage=space.homepage, parent=space.parent)
        if request.method == 'GET':
            form.title.data = title
            form.description.data = description
        form.homepage.choices = [(page.id, page.title) for page in Page.query.filter(or_(Page.parent == None, Page.space == int(sid))).all()]
        parent_choices = [(space.id, space.name) for space in Spaces.query.all()]
        parent_choices.insert(0, (None, "Без родителя"))
        form.parent.choices = parent_choices

        if form.is_submitted():
            ref = request.referrer.split("/")[-1]
            if "space?id=" in ref:
                sid = ref.split("id=")[-1]
            n_title = form.title.data
            
            n_homepage = form.homepage.data
            if n_homepage == "None":
                n_homepage = None
            n_parent = form.parent.data
            
            if n_parent == "None":
                n_parent = None
            
            n_description = form.description.data
            print(n_description)
            
            db.session.begin()
            if form.img.data:
                n_img = form.img.data
                filename = secure_filename(n_img.filename)
                print(filename)
                pre_path = os.path.join(app.config["UPLOAD_FOLDER"])
                path = uniquify(f"{pre_path}/{filename}")
                filename = path.split("/")[-1]
                n_img.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                img_path = f'{UPLOAD_FOLDER}/{filename}'
                space.logo = img_path

            space = Spaces.query.get(sid)
            space.name = n_title
            space.description = n_description
            space.homepage = n_homepage
            space.parent = n_parent
            
            db.session.commit()
            db.session.close()

            return redirect(url_for('spaces'))

        return render_template('space.html', title=title, id=sid, form=form, logo=logo)
    else:
        return redirect(url_for('index'))


@app.route("/profile", methods=("GET", "POST"))
@login_required
def profile():
    list = []

    for page in Page.query.filter(Page.author == current_user.username).all():
        creation_date = datetime.fromtimestamp(int(page.date)).strftime("%Y-%m-%d %H:%M")
        last_ver = Versions.query.filter(Versions.page_id == page.id).order_by(desc(Versions.version)).first()
        if last_ver is None:
            last_edit = '-'
            edit_author = '-'
        else:
            last_edit = datetime.fromtimestamp(int(last_ver.time)).strftime("%Y-%m-%d %H:%M")
            edit_author = last_ver.author

        item = {
            'id': page.id,
            'title': page.title,
            'creation_date': creation_date,
            'last_edit': last_edit,
            'edit_author': edit_author,
        }
        list.append(item)

    return render_template('profile.html', list=list)


@app.route("/fav", methods=["POST"])
@login_required
def fav():
    try:
        sid = request.args['space']
    except KeyError:
        try:
            pid = request.args['page']
        except KeyError:
            return render_template('404.html')
    
    if sid:
        print(sid)
        db.session.begin()
        spaces = current_user.fav_spaces
        if spaces is None or spaces == r'{}':
            spaces = []
        else:
            spaces = spaces[1:-1].split(',')

        if request.args['action'] == 'add':
            print('add')
            spaces.append(sid)
            current_user.fav_spaces = spaces
        elif request.args['action'] == 'remove':
            print('remove')
            spaces.remove(sid)
            if spaces == ['']:
                spaces = None
            current_user.fav_spaces = spaces
        print(spaces)
        db.session.commit()
        db.session.close()

        return dumps({'status': 'done'})

    if pid:
        return dumps({'status': 'done'})

@app.route("/tree/<space>")
@login_required
def page_tree_gen(space):
    ref = request.referrer.split("/")[-1]
    if "page?id=" in ref:
        ref_id = ref.split("id=")[-1]
    else:
        ref_id = 0

    if current_user.forbidden_pages != "{}":
        p_list = current_user.forbidden_pages[1:-1].split(",")
        print(p_list)
        pages = (
            Page.query.filter(and_(Page.space == space, not_(Page.id.in_(p_list))))
            .order_by(or_(desc(Page.parent), Page.date))
            .all()
        )
    else:
        pages = Page.query.filter(and_(Page.space == space)).order_by(Page.date).all()

    tree_structure = []

    for page in pages:
        pageObj = {}
        pageObj["id"] = page.id
        if page.parent == 0 or page.parent is None:
            pageObj["parent"] = "#"
            pageObj["state"] = {"opened": True}
        else:
            pageObj["parent"] = page.parent
            if page.id == int(ref_id):
                pageObj["state"] = {"opened": True, "selected": True}
            else:
                pageObj["state"] = {"selected": False}
        pageObj["text"] = page.title
        tree_structure.append(pageObj)

    return dumps(tree_structure)


@app.route("/search/<query>", methods=["GET"])
def search(query):
    db.session.begin()
    es_resp = app.elasticsearch.search(
        index="posts",
        body={
            "query": {
                "bool": {
                    'should': [{'match': {"title": query}}, {'match': {"text": query}}]}
            }
        },
    )
    result = []
    for hit in es_resp["hits"]["hits"]:
        page_id = hit["_id"]
        page = Page.query.get(page_id)
        title = page.title
        result.append({"id": page_id, "title": title[:30]})

    db.session.close()
    if len(result) > 0:
        return dumps(result, ensure_ascii=False)
    else:
        return "200"


@app.route("/esreindex")
def esreindex():
    db.session.begin()
    app.elasticsearch.indices.delete(index="posts")
    posts = Page.query.all()
    for post in posts:
        id = post.id
        title = post.title
        post_text_soup = BeautifulSoup(post.text, "html.parser")
        post_text = post_text_soup.text
        post = {
            "title": title,
            "text": post_text,
        }
        es_resp = app.elasticsearch.index(index="posts", id=id, body=post)
        print(es_resp)
    db.session.commit()
    db.session.close()
    return "Done"


@app.route("/users_edit", methods=("GET", "POST"))
@login_required
def user_edit():
    if current_user.role is not None:
        if "Admin" in current_user.role:
            user_list = [
                {
                    "id": user.id,
                    "username": user.username,
                    "name": user.name,
                    "mail": user.email,
                    "role": user.role,
                    "user_pic": user.user_pic,
                    "confirmed": user.confirmed,
                    "last_online": datetime.fromtimestamp(
                        int(user.last_online)
                    ).strftime("%Y-%m-%d %H:%M"),
                    "is_active": user.is_active,
                }
                for user in User.query.all()
            ]
            return render_template("admin.html", users=user_list)
        else:
            return url_for("index")
    else:
        return url_for("index")


@app.route("/permissions_edit", methods=("GET", "POST"))
@login_required
def perm_edit():
    if "Admin" in current_user.role:
        uid = request.args["id"]
        user = User.query.get(uid)
        perm_form = permission_form()
        perm_form.spaces.choices = [
            (space.id, space.name)
            for space in Spaces.query.order_by(Spaces.id, Spaces.parent).all()
        ]
        if user.allowed_spaces:
            perm_form_spaces = user.allowed_spaces
            perm_form_spaces = perm_form_spaces[1:-1].split(",")
        else:
            perm_form_spaces = []

        perm_form.pages.choices = [
            (page_r.id, page_r.title)
            for page_r in Page.query.order_by(Page.parent, Page.id).all()
        ]
        if user.forbidden_pages:
            perm_form.spaces.default = [user.forbidden_pages]

        if perm_form.is_submitted():
            new_spaces = list(perm_form.spaces.data)
            print(new_spaces)
            new_pages = perm_form.pages.data
            print(new_pages)
            db.session.begin()
            user.allowed_spaces = new_spaces
            user.forbidden_pages = new_pages
            db.session.commit()

            # Space members recount
            spaces = Spaces.query.all()
            users = User.query.all()
            db.session.begin()
            for space in spaces:
                counter = 0
                for user in users:
                    if str(space.id) in user.allowed_spaces[1:-1].split(","):
                        counter += 1
                space.members = counter

            db.session.commit()
            db.session.close()

            return redirect(url_for("user_edit"))

        return render_template("perm.html", perm=perm_form, def_spaces=perm_form_spaces)

    else:
        return url_for("index")


@app.route("/gallery", methods=("GET", "POST"))
def gallery_fix():
    img_list_raw = request.data
    print(img_list_raw)
    img_list = loads(img_list_raw)
    print(img_list)

    gid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    img = [
        {
            'num': int(img),
            'link': img_list[img]

        } for img in img_list.keys()]
    print(img)
    num = len(img)

    return str(render_template('gallery_template.html', id=gid, gallery=img, num=num))


@app.route("/eagle", methods=("GET", "POST"), strict_slashes=False)
def eagle_index():
    if current_user.is_authenticated:
        try:
            request.args['space']
        except KeyError:
            parent = None
        else:
            parent = request.args['space']

        if current_user.fav_spaces:
            fav_list = current_user.fav_spaces[1:-1].split(",")
        else:
            fav_list = []
        if current_user.allowed_spaces:
            s_list = current_user.allowed_spaces[1:-1].split(",")
            spaces_raw = Spaces.query.filter(and_(Spaces.parent == parent, Spaces.id.in_(s_list))).order_by(desc(Spaces.id.in_(fav_list))).all()
        else:
            if current_user.role == "Admin":
                spaces_raw = Spaces.query.filter(Spaces.parent == parent).order_by(desc(Spaces.id.in_(fav_list))).all()
            else:
                spaces_raw = []

        if len(spaces_raw) < 1:
            p = Spaces.query.get(parent)
            try:
                homepage_id = p.homepage
            except AttributeError:
                return render_template('ftu.html')
            else:    
                return redirect(url_for('page', id=homepage_id))

        spaces = [
            {
                "id": space.id,
                "parrent": space.parent,
                "name": space.name,
                "image": space.logo,
                "members": space.members,
                "description": space.description,
                "homepage": space.homepage,
            }
            for space in spaces_raw
        ]
        
        fav_list = dumps(fav_list)
    else:
        spaces = []
        fav_list = []

    return render_template("eagle.html", title="Главная", spaces=spaces, action="main", fav=fav_list, origin='eagle')


@app.route("/eagle/task", methods=("GET", "POST"), strict_slashes=False)
@login_required
def eagle_task():
    return render_template('task.html')


@app.route("/eagle/tasks", methods=("GET", "POST"), strict_slashes=False)
@login_required
def eagle_user_tasks():
    return


@app.route("/eagle/create", methods=("GET", "POST"), strict_slashes=False)
@login_required
def eagle_create_tasks():


    projects = [
        {
            'key': project.key,
            'name': project.name
        } for project in Spaces.query.filter(Spaces.key != None).all()
    ]

    return render_template('task_create.html', origin="eagle", title='Новая задача', project_list=projects)


@app.route("/api/task", methods=("GET", "POST", "PATCH", "DELETE"))
@login_required
def task_api():
    q_param = request.args

    id = q_param.get('id')
    action = q_param.get('action')
    assignee = q_param.get('assignee')
    status = q_param.get('status')
    '''
    Status code:
    1: To do (Default)
    2: In progress
    3: Review
    4: Test
    5: Done
    '''
    priority = q_param.get('priority')
    '''
    Priority code:
    1: Lowest
    2: Low
    3: Medium (Default)
    4: High
    5: Highest
    6: Blocker
    '''
    data = q_param.get('data')

    limit = q_param.get('limit')
    offset = q_param.get('offset')

    types = {'Задача':'task', 'Ошибка':'error', 'Эпик':'epic', 'История':'story'}
    priorities = {'Lowest':1, 'Low':2, 'Medium':3, 'High':4, 'Highest':5, 'Blocker':6}

    if request.method == "GET":
        if id:
            return dumps(Tasks.query.get(id))
            
    if request.method == "POST":
        if not id:
            data = loads(request.data)
            
            
            name = data['title']
            project = data['project']
            project_id_raw = Tasks.query.filter(Tasks.project_key == project).all()
            project_id = len(project_id_raw) + 1
            description = data['description']
            date = int(time.time())
            type_raw = data['type']
            type = types[type_raw]
            priority_raw = data['priority']
            priority = priorities[priority_raw]
            if data['tags']:
                tags = data['tags']
            else:
                tags = None
            if data['attach']:
                attach = data['attach']
            else:
                attach = None

            assignee = data['assignee']

            db.session.begin()
            task = Tasks(name, project, description, project_id=project_id, author=current_user, date_creation=date, type=type, priority=priority, tags=tags, attach=attach, assignee=assignee)
            db.session.commit(task)
            db.session.close()

            return dumps({'result': 'Task created'})

    if request.method == "PATCH":
        if id:
            task = Tasks.query.get(id)
            #update
            return

    if request.method == "DELETE":
        if id:
            db.session.begin()
            task = Tasks.query.get(id)
            db.session.delete(task)
            db.session.close()
            return dumps({ 'result': 'Task deleted'})

    return


@app.route("/page_upload", methods=("GET", "POST"))
@login_required
def upload_pages():
    list = []

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en,ru;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        "Connection": "keep-alive",
        "DNT": "1",
        "Host": "confluence.abinmetall.ru",
        "Referer": "https://confluence.abinmetall.ru/pages/reorderpages.action?key=BRG&openId=18912383",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.66 Safari/537.36",
    }

    cookie = {
        "PBack": "0",
        "PrivateComputer": "true",
        "cookiesession1": "678A8C38F9FE08437CBFCDA08878B586",
        "seraph.confluence": "36274180%3A0a059f7322cc8a33f035e2edbb73181cbb900e8e",
        "confluence.list.pages.cookie": "list-content-tree",
        "confluence.browse.space.cookie": "space-attachments",
        "confluence.last-web-item-clicked": "system.space.tools%2Foverview%2Fspacedetails",
        "JSESSIONID": "E12FCDF359CD4D31E7407BE3ACF45C8B",
    }

    # for link in list:
    #     req = requests.get(link['link'], headers=headers, cookies=cookie, verify=False)
    #     resp = req.text
    #     l_soup = BeautifulSoup(resp, "html.parser")
    #     text = str(l_soup.find(id='main-content'))
    #     title = link['name']
    #     print(title)
    #     db.session.begin()
    #     date = int(time.time())
    #     new_page = Page(
    #         title=title,
    #         author='e.yaskov',
    #         text=text,
    #         date=date,
    #         parent=38,
    #         space=14,
    #         limitations=None,
    #     )

    #     db.session.add(new_page)
    #     db.session.commit()
    #     db.session.close()

    return "Done"


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5004, debug=True)
