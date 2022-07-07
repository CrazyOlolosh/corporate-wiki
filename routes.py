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
    g
)

from datetime import datetime, timedelta
import time
from sqlalchemy import desc, and_, not_, null
from sqlalchemy.orm import joinedload
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

from flask_mail import Message

from app import create_app, db, login_manager, bcrypt, mail
from models import Spaces, User, Page, Versions, Comments
from forms import comment_form, login_form, register_form, post_form, permission_form


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
    if current_user.is_authenticated:
        db.session.begin()
        
        if current_user.allowed_spaces:
            s_list = current_user.allowed_spaces[1:-1].split(',')
            print(s_list)
            spaces_raw = Spaces.query.filter(Spaces.id.in_(s_list)).all()
        else:
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
    else:
        spaces = []
    return render_template("index.html", title="Home", spaces=spaces, action='main')


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
            username = str(email).split('@')[0]
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
    ref = request.referrer.split('/')[-1]
    if 'page?id=' in ref:
        ref_id = ref.split('id=')[-1]
        ref_page = Page.query.get(ref_id)
        space_default = ref_page.space
        parent_default = ref_page.parent
        form = post_form(space=space_default, parent=parent_default)
        if current_user.forbidden_pages != '{}':
            p_list = current_user.forbidden_pages[1:-1].split(',')
            parent_choices = [(page.id, page.title) for page in Page.query.filter(and_(Page.space == space_default, not_(Page.id.in_(p_list)))).order_by(Page.parent, Page.id).all()]
        else:
            parent_choices = [(page.id, page.title) for page in Page.query.filter(Page.space == space_default).order_by(Page.parent, Page.id).all()]
        parent_choices.insert(0, (None, 'Без родителя'))
        form.parent.choices = parent_choices
    else:
        form = post_form()

    if current_user.allowed_spaces:
        s_list = current_user.allowed_spaces[1:-1].split(',')
        form.space.choices = [(space.id, space.name) for space in Spaces.query.filter(Spaces.id.in_(s_list)).order_by(Spaces.parent, Spaces.id).all()]
    else:
        form.space.choices = [(space.id, space.name) for space in Spaces.query.order_by(Spaces.parent, Spaces.id).all()]

    if form.is_submitted():
        text = form.post.data
        text = text.replace('\n','')
        text = text.replace('\\n','')
        if '\n' in text:
            print('Catch newline!')
        title = form.heading.data
        print(form.parent.data)
        if form.parent.data == "None":
            parent = None
        else:
            parent = form.parent.data
        print(type(parent))
        space = form.space.data
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
       
        db.session.begin()
        page = Page.query.filter(Page.author == current_user.username).order_by(desc(Page.date)).first()
        page_id = page.id
        post_text_soup = BeautifulSoup(text, "html.parser")
        post_text = post_text_soup.text
        post = {
            'text': post_text,
        }
        es_resp = app.elasticsearch.index(index="posts", id=page_id, body=post)
        print(es_resp)
        db.session.commit()
        db.session.close()

        return redirect(url_for('page', id=page_id))

    return render_template('create.html', action="create", form=form, title="Новая запись")


@app.route('/edit', methods=("GET", "POST"), strict_slashes=False)
@login_required
def edit():
    if request.method == "GET":
        try:
            id = request.args['id']
        except KeyError:
            return render_template(url_for('page_not_found'))

    if request.method == "POST":
        ref = request.referrer.split('/')[-1]
        if '?id=' in ref:
            id = ref.split('id=')[-1]
    
    page = Page.query.get(id)
    form = post_form(space=page.space, parent=page.parent)
    form.heading.data = page.title
    parent_choices = [(page_r.id, page_r.title) for page_r in Page.query.filter(Page.space == page.space).order_by(Page.parent, Page.id).all()]
    parent_choices.insert(0, (None, 'Без родителя'))
    form.parent.choices = parent_choices

    if current_user.allowed_spaces:
        s_list = current_user.allowed_spaces[1:-1].split(',')
        form.space.choices = [(space.id, space.name) for space in Spaces.query.filter(Spaces.id.in_(s_list)).order_by(Spaces.parent, Spaces.id).all()]
    else:
        form.space.choices = [(space.id, space.name) for space in Spaces.query.order_by(Spaces.parent, Spaces.id).all()]

    page_text = page.text
    page_text = page_text.replace('"','\\"')
    page_text = page_text.replace('\n','')
    if '\n' in page_text:
        print('!Catch!')
    page_title = page.title

    versions_list = [
    {
        'id': version.id,
        'version': version.version,
        'author': version.v_author.name,
        'time': datetime.fromtimestamp(int(version.time)).strftime('%Y-%m-%d %H:%M')
    } 
    for version in Versions.query.filter(Versions.page_id == id).order_by(Versions.version).all()]


    if form.is_submitted():
        text = form.post.data
        text = text.replace('\n','')
        text = text.replace('\\n','')
        if '\n' in text:
            print('!Catch!')
        title = form.heading.data
        parent = form.parent.data
        if parent == 'None':
            parent = None
        space = form.space.data
        limitations = ''

        date = int(time.time())
        db.session.begin()
        ver_num = len(Versions.query.filter(Versions.page_id == page.id).all())
        new_backup = Versions(
            page_id=page.id,
            version=ver_num + 1,
            title=page.title,
            text=page.text.replace('\n',''),
            author=current_user.username,
            time=date
        )

        print(page.p_author.email)
        msg = Message(subject=f'Изменение страницы {page.title}', recipients=[page.p_author.email], body='В созданной вами станице произошли изменения', sender='notify@kindofconfluence.com')  

        page.title = title
        page.text = text
        page.space = space
        page.parent = parent

        db.session.add(new_backup)
        
        post_text_soup = BeautifulSoup(text, "html.parser")
        post_text = post_text_soup.text
        post = {
            'text': post_text,
        }
        es_resp = app.elasticsearch.index(index="posts", id=page.id, body=post)
        print(es_resp)
        db.session.commit()
        db.session.close()

        # mail.send(msg)  # Unable from localhost

        return redirect(url_for('page', id=id))

    return render_template('create.html', action="edit", form=form, title="Редактирование", text=page_text, p_title=page_title, versions=versions_list)


@app.route('/preview', methods=("GET", "POST"), strict_slashes=False)
@login_required
def preview():
    pre_id = request.args['id']
    version = Versions.query.get(pre_id)
    title = version.title
    pid = version.page_id
    text = version.text
    return render_template('preview.html', id=pid, title=title, text=text, action='preview')


@app.route('/restore', methods=("GET", "POST"), strict_slashes=False)
@login_required
def restore():
    if 'edit?id=' in request.referrer:
        pre_id = request.args['id']
        db.session.begin()
        # Update current page from version and remove newer
        version = Versions.query.get(pre_id)
        page = Page.query.get(version.page_id)
        
        page.text = version.text
        page.title = version.title

        remove_versions = Versions.query.filter(and_(Versions.version > version.version, Versions.page_id == version.page_id))
        db.session.delete(remove_versions)

        db.session.commit()
        db.session.close()
        
        return render_template(url_for('page', id=version.page_id))
    else:
        return render_template(url_for('index'))


@app.route('/page', methods=("GET", "POST"))
@login_required
def page():
    
    comment = comment_form()
    if request.method == "GET":
        try:
            id = request.args['id']
        except KeyError:
            return render_template('404.html')
        
        try:
            page_note = Page.query.get(id)
            title = page_note.title
            text = page_note.text
            space = page_note.space
        except AttributeError:
            return render_template('404.html')
        
        comments_list = [
            {
                'text': comment.text,
                'author': comment.c_author.name,
                'author_img': comment.c_author.user_pic,
                'author_active': comment.c_author.is_active,
                'time': datetime.fromtimestamp(int(comment.time)).strftime('%Y-%m-%d %H:%M')
            } 
            for comment in Comments.query.filter(Comments.page_id == id).order_by(Comments.time).all()]

        return render_template('page.html', id=id, title=title, text=text, space=space, comment=comment, comments=comments_list, action='page')

    if comment.is_submitted():
        ref = request.referrer.split('/')[-1]
        if 'page?id=' in ref:
            id = ref.split('id=')[-1]
        date = int(time.time())
        com_text = comment.text.data
        page_id = id
        author = current_user.id
        c_time = date

        db.session.begin()
        new_comment = Comments(page_id=page_id, author=author, text=com_text, time=c_time)
        db.session.add(new_comment)
        db.session.commit()
        db.session.close()

        return redirect(url_for('page', id= id))


@app.route('/spaces', methods=("GET", "POST", "DELETE", "PATCH"))
@login_required
def spaces():
    if request.method == "GET":
        if current_user.allowed_spaces:
            s_list = current_user.allowed_spaces[1:-1].split(',')
            spaces_raw = Spaces.query.filter(Spaces.id.in_(s_list)).all()
        else:
            spaces_raw = Spaces.query.all()


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

        return render_template("spaces.html", title="Пространства", spaces=spaces, action='space')


@app.route('/tree/<space>')
@login_required
def page_tree_gen(space):
    ref = request.referrer.split('/')[-1]
    if 'page?id=' in ref:
        ref_id = ref.split('id=')[-1]
    else:
        ref_id = 0

    if current_user.forbidden_pages != '{}':
        p_list = current_user.forbidden_pages[1:-1].split(',')
        print(p_list)
        pages = Page.query.filter(and_(Page.space == space, not_(Page.id.in_(p_list)))).all()
    else:
        pages = Page.query.filter(and_(Page.space == space)).all()

    tree_structure = []

    for page in pages:
        pageObj = {}
        pageObj['id'] = page.id
        if page.parent == 0 or page.parent is None:
            pageObj['parent'] = '#'
            pageObj['state'] = {'opened': True}
        else:
            pageObj['parent'] = page.parent
            if page.id == int(ref_id):
                pageObj["state"] = {'opened': True, 'selected': True}
            else:
                pageObj["state"] = {'selected': False}
        pageObj['text'] = page.title
        tree_structure.append(pageObj)

    return dumps(tree_structure)


@app.route('/search/<query>', methods=["GET"])
def search(query):
    db.session.begin()
    es_resp = app.elasticsearch.search(index='posts', body={'query': {'match': {'text': query}}})
    result = []
    for hit in es_resp['hits']['hits']:
        page_id = hit['_id']
        page = Page.query.get(page_id)
        title = page.title
        result.append({'id': page_id, 'title': title[:30]})

    db.session.close()
    if len(result) > 0:
        return dumps(result, ensure_ascii=False)
    else:
        return


@app.route('/esreindex')
def esreindex():
    db.session.begin()
    posts = Page.query.all()
    for post in posts:
        id = post.id
        post_text_soup = BeautifulSoup(post.text, "html.parser")
        post_text = post_text_soup.text
        post = {
            'text': post_text,
        }
        es_resp = app.elasticsearch.index(index="posts", id=id, body=post)
        print(es_resp)
    db.session.commit()
    db.session.close()
    return "Done"


@app.route('/users_edit', methods=("GET", "POST"))
@login_required
def user_edit():
    if 'Admin' in current_user.role:
        user_list = [
            {
                'id': user.id,
                'username': user.username,
                'name': user.name,
                'mail': user.email,
                'role': user.role,
                'user_pic': user.user_pic,
                'confirmed': user.confirmed,
                'last_online': datetime.fromtimestamp(int(user.last_online)).strftime('%Y-%m-%d %H:%M'),
                'is_active': user.is_active,

            } for user in User.query.all()
        ]
        return render_template('admin.html', users=user_list)
    else:
        return(url_for('index'))


@app.route('/permissions_edit', methods=("GET", "POST"))
@login_required
def perm_edit():
    if 'Admin' in current_user.role:
        uid = request.args['id']
        user = User.query.get(uid)
        perm_form = permission_form()
        perm_form.spaces.choices = [(space.id, space.name) for space in Spaces.query.order_by(Spaces.id, Spaces.parent).all()]
        if user.allowed_spaces:
            perm_form_spaces = user.allowed_spaces
            perm_form_spaces = perm_form_spaces[1:-1].split(',')
        else:
            perm_form_spaces = []
        
        perm_form.pages.choices = [(page_r.id, page_r.title) for page_r in Page.query.order_by(Page.parent, Page.id).all()]
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

            #Space members recount
            spaces = Spaces.query.all()
            users = User.query.all()
            db.session.begin()
            for space in spaces:
                counter = 0
                for user in users:
                    if str(space.id) in user.allowed_spaces[1:-1].split(','):
                        counter += 1
                space.members = counter

            db.session.commit()
            db.session.close()
            
            return redirect(url_for('user_edit'))

        return render_template('perm.html', perm=perm_form, def_spaces=perm_form_spaces)
    
    else:
        return(url_for('index'))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
