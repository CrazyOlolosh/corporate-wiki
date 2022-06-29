from types import NoneType
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
    make_response
)

from datetime import datetime, timedelta
import time
from sqlalchemy import desc
from sqlalchemy.exc import (
    IntegrityError,
    DataError,
    DatabaseError,
    InterfaceError,
    InvalidRequestError,
)
from werkzeug.routing import BuildError


from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)

from app import create_app, db, login_manager, bcrypt
from models import Spaces, User, Page
from forms import login_form, register_form, post_form

import threading
from json import dumps
import re
import requests
from httplib2 import Http
from bs4 import BeautifulSoup
from flask_cors import CORS
import os


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app = create_app()
CORS(app)


@app.before_request
def session_handler():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=720)


@app.route("/", methods=("GET", "POST"), strict_slashes=False)
def index():
    db.session.begin()
    spaces_raw = Spaces.query.all()
    db.session.close()
    
    spaces = [
        {
            'id': space.id,
            'parrent': space.parent,
            'name': space.name,
            'image': space.logo,
            'members': space.members,
            'description': space.description,
            'homepage': space.homepage,
        }
        for space in spaces_raw
    ]
    return render_template("index.html", title="Home", spaces=spaces)


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
                flash("Invalid Username or password!", "danger")
        except Exception as e:
            flash(e, "danger")

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
            username = str(email).split('@')[0]

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
    return render_template('404.html'), 404


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route('/create', methods=("GET", "POST"), strict_slashes=False)
@login_required
def post():
    form = post_form()
    if form.is_submitted():
        text = form.post.data
        title = form.heading.data
        print(title)
        parent = ''
        space = ''
        limitations = ''

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

        page = Page.query.filter(Page.author == current_user.username).order_by(desc(Page.date)).first()
        page_id = page.id
        db.session.close()

        return redirect(url_for('page', id=page_id))
        
    return render_template('create.html',form=form, title="Новая запись")


@app.route('/imageuploader', methods=['POST'])
@login_required
def imageuploader():
    file = request.files.get('file')
    if file:
        filename = file.filename.lower()
        fn, ext = filename.split('.')
        # truncate filename (excluding extension) to 30 characters
        fn = fn[:30]
        fn = fn.replace(' ', '_')
        filename = fn + '.' + ext
        print(filename)
        if ext in ['jpg', 'gif', 'png', 'jpeg']:
            img_fullpath = os.path.join("./static/uploads", filename)
            file.save(img_fullpath)
            return jsonify({'location' : filename})

    # fail, image did not upload
    output = make_response(404)
    output.headers['Error'] = 'Image failed to upload'
    return output


@app.route('/page', methods=("GET", "DELETE", "PATCH"))
@login_required
def page():
    id = request.args['id']
    if request.method == "GET":
        try:
            page_note = Page.query.get(id)
            title = page_note.title
            text = page_note.text
        except AttributeError:
            return render_template('404.html')


        return render_template('page.html', title=title, text=text)


@app.route('/spaces', methods=("GET", "POST", "DELETE", "PATCH"))
@login_required
def spaces():
    if request.method == "GET":
        db.session.begin()
        spaces_raw = Spaces.query.all()
        db.session.close()

        spaces = [
            {
                'id': space.id,
                'parrent': space.parent,
                'name': space.name,
                'image': space.logo,
                'members': space.members,
                'description': space.description,
                'homepage': space.homepage,
            }
            for space in spaces_raw
        ]

        return render_template("spaces.html", title="Пространства", spaces=spaces)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
