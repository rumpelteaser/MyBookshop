# --------------- Blog with Users - Forms Module --------------- #

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForms

class CreateBookForm(FlaskForm):
    title = StringField("Book Title", validators=[DataRequired()])
    author = StringField("Author", validators=[DataRequired()])
    #img_url = StringField("Book Image URL", validators=[DataRequired(), URL()])
    img_url = StringField("Book Image URL", validators=[DataRequired()])
    body = CKEditorField("Book Description", validators=[DataRequired()])
    submit = SubmitField("Enter Book")


class CreateRegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("E-Mail", validators=[DataRequired()])
    password = StringField("password", validators=[DataRequired()])
    submit = SubmitField("Submit")


class CreateLoginForm(FlaskForm):
    email = StringField("E-Mail", validators=[DataRequired()])
    password = StringField("password", validators=[DataRequired()])
    submit = SubmitField("Submit")


class CreateCommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")
