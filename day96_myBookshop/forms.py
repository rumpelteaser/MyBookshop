# --------------- Blog with Users - Forms Module --------------- #

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FloatField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForms

class CreateBookForm(FlaskForm):
    title = StringField("Book Title", validators=[DataRequired()])
    author = StringField("Author", validators=[DataRequired()])
    #img_url = StringField("Book Image URL", validators=[DataRequired(), URL()])
    img_url = StringField("Book Image URL", validators=[DataRequired()])
    price = FloatField("Price", validators=[DataRequired()])
    body = CKEditorField("Book Description", validators=[DataRequired()])
    submit = SubmitField("Enter Book")


class CreateRegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("E-Mail", validators=[DataRequired()])
    password = PasswordField("password", validators=[DataRequired()])
    submit = SubmitField("Submit")


class CreateLoginForm(FlaskForm):
    email = StringField("E-Mail", validators=[DataRequired()])
    password = PasswordField("password", validators=[DataRequired()])
    submit = SubmitField("Submit")
