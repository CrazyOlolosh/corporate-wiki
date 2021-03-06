from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    IntegerField,
    DateField,
    TextAreaField,
    SubmitField,
    SelectField,
    SelectMultipleField
)

from flask import request
from flask_babel import _, lazy_gettext as _l

from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms.validators import InputRequired, Length, EqualTo, Email, Regexp, Optional, DataRequired
import email_validator
from flask_login import current_user
from wtforms import ValidationError, validators
from models import User


class login_form(FlaskForm):
    email = StringField(validators=[InputRequired(), Email(), Length(1, 64)])
    pwd = PasswordField(validators=[InputRequired(), Length(min=8, max=72)])
    # Placeholder labels to enable form rendering
    username = StringField(validators=[Optional()])


class register_form(FlaskForm):
    name = StringField(
        validators=[
            InputRequired(),
            Length(3, 20, message="Please provide a valid name"),
            Regexp(
                "^[A-Za-zА-Яа-я][A-Za-zА-Яа-я0-9_. ]*$",
                0,
                "Usernames must have only letters, " "numbers, dots or underscores",
            ),
        ]
    )
    email = StringField(validators=[InputRequired(), Email(), Length(1, 64)])
    pwd = PasswordField(validators=[InputRequired(), Length(8, 72)])
    cpwd = PasswordField(
        validators=[
            InputRequired(),
            Length(8, 72),
            EqualTo("pwd", message="Passwords must match !"),
        ]
    )

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError("Email already registered!")

    def validate_uname(self, uname):
        if User.query.filter_by(username=uname.data).first():
            raise ValidationError("Username already taken!")


class post_form(FlaskForm):
    heading = StringField('Заголовок', validators=[InputRequired(), Length(max=100)])
    post = TextAreaField('Основной текст', validators=[InputRequired()])
    space = SelectField('Пространство', choices=[])
    parent = SelectField('Родитель', choices=[])


class comment_form(FlaskForm):
    text = TextAreaField("Комментарии", render_kw={'placeholder': 'Напишите Ваш комментарий...', 'rows': 4}, validators=[InputRequired()])


class permission_form(FlaskForm):
    pages = SelectMultipleField("Запрещенные страницы", choices=[])
    spaces = SelectMultipleField("Разрешенные пространства", choices=[])


class space_form(FlaskForm):
    title = StringField('Название пространства', validators=[InputRequired(), Length(max=100)])
    homepage = SelectField('Домашняя страница', choices=[])
    parent = SelectField('Родитель', choices=[])
    description = TextAreaField("Описание", render_kw={'rows': 5}, validators=[InputRequired()])
    img = FileField('Логотип пространства')
