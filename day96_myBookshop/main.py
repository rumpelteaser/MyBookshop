# =============== Blog with Users - Main Module =============== #

# --------------- Perform Initializations --------------- #

# Import needed modules
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, CreateRegisterForm, CreateLoginForm, CreateCommentForm
from functools import wraps
from flask_gravatar import Gravatar
import os

# Create Flask Application
app = Flask(__name__)
if os.environ.get("SECRET_KEY"):    # get environment variable
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
else:   # get constant
    app.config['SECRET_KEY'] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
ckeditor = CKEditor(app)
Bootstrap(app)

# Define default backup image and gravatar link
post_img = "https://images.unsplash.com/photo-1530482054429-cc491f61333b?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1651&q=80"
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# Connect Flask App to DB
if os.environ.get("DATABASE_URL"):  # Use PostGRES
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
else:   # Use SQLite
    print("Using Local DB")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Create DB Tables

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    # This will act like a list of BlogPost objects attached to each User.
    # The "author" refers to the 'author' property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")
    # This will act like a list of Comment objects attached to each User.
    # The "comment_author" refers to the 'comment_author' property in the Comment class.
    comments = relationship("Comment", back_populates="comment_author")

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    # Create Foreign Key, in "users.id" 'users' refers to the tablename of User.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, "posts" refers to the 'posts' property in the User class.
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    # This will act like a list of Comment objects attached to each BlogPost.
    # The "parent_post" refers to the 'parent_post' property in the Comment class.
    comments = relationship("Comment", back_populates="parent_post")

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    # Create Foreign Key, in "users.id" 'users' refers to the tablename of User.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, "comments" refers to the 'comments' property in the User class.
    comment_author = relationship("User", back_populates="comments")
    # Create Foreign Key, in "blog_posts.id" 'blog_posts' refers to the tablename of BlogPost.
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    # Create reference to the BlogPost object, "comments" refers to the 'comments' property in the User class.
    parent_post = relationship("BlogPost", back_populates="comments")

db.create_all()

# Create a Login Manager and connect it to Flask Application
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Define a decorator to allow access only to Administrators
def admin_only(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return function(*args, **kwargs)
    return decorated_function


# --------------- Define Routes and related callback functions --------------- #


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html",
                           all_posts=posts,
                           logged_in=current_user.is_authenticated)


@app.route('/register', methods=["GET", "POST"])
def register():
    register_form = CreateRegisterForm()
    if request.method == "POST":
        print("Registering new user")
        # get email info and check if already present in the DB
        email = register_form.email.data
        user = db.session.query(User).filter_by(email=email).first()
        if not user:
            # Get name and password info entered by user
            name = register_form.name.data
            password = register_form.password.data
            # Encrypt the password
            hashed_password = generate_password_hash(password,
                                                     method='pbkdf2:sha256',
                                                     salt_length=8)
            # Insert new user in the DB
            print("Registering ", name, email, hashed_password)
            new_user = User(name=name,
                            email=email,
                            password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            # Log in and authenticate user after adding details to database
            login_user(new_user)
            # Return to main page
            return redirect(url_for('get_all_posts'))
        else:
            flash("You already registered that email, log in instead !")
            return redirect(url_for('login'))
    else:
        return render_template("register.html",
                               form=register_form,
                               logged_in=current_user.is_authenticated)


@app.route('/login', methods=["GET", "POST"])
def login():
    login_form = CreateLoginForm()
    if request.method == "POST":
        # Get info entered by user
        email = login_form.email.data
        password = login_form.password.data
        print("Login request by ", email, password)
        # Look if specified email exist in the DB (if so, it is unique)
        user = db.session.query(User).filter_by(email=email).first()
        # If user exist, log in
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                flash("Sorry, wrong password.")
                return redirect(url_for('login'))
        else:
            flash("Sorry, unknown user.")
            return redirect(url_for('login'))
    else:
        # Present Login form to user
        return render_template("login.html",
                               form=login_form,
                               logged_in=current_user.is_authenticated)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    comment_form = CreateCommentForm()
    if request.method == "POST":
        if current_user.is_authenticated:
            new_comment = Comment(author_id=current_user.id,
                                  post_id=requested_post.id,
                                  text=comment_form.comment_text.data)
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for('get_all_posts'))
        else:
            flash("Sorry, you have to login to post comments.")
            return redirect(url_for('login'))
    else:
        return render_template("post.html",
                               post=requested_post,
                               form=comment_form,
                               logged_in=current_user.is_authenticated,
                               comments=requested_post.comments)


@app.route("/about")
def about():
    return render_template("about.html", logged_in=current_user.is_authenticated)


@app.route("/contact")
def contact():
    return render_template("contact.html", logged_in=current_user.is_authenticated)


@app.route("/new-post", methods=["GET", "POST"])
@login_required
@admin_only
def add_new_post():
    post_form = CreatePostForm()
    if request.method == "POST":
        if post_form.validate_on_submit():
            print("Adding post")
            new_post = BlogPost(
                title=post_form.title.data,
                subtitle=post_form.subtitle.data,
                body=post_form.body.data,
                #img_url=form.img_url.data,
                img_url=post_img,
                author=current_user,
                date=date.today().strftime("%B %d, %Y")
                )
            print("post created")
            db.session.add(new_post)
            db.session.commit()
            print("post added")
            return redirect(url_for("get_all_posts"))
        else:
            print("Form not validated")
            return redirect(url_for("get_all_posts"))
    else:
        return render_template("make-post.html",
                               form=post_form,
                               logged_in=current_user.is_authenticated)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@login_required
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
        )
    if request.method == "POST":
        if edit_form.validate_on_submit():
            post.title = edit_form.title.data
            post.subtitle = edit_form.subtitle.data
            post.img_url = edit_form.img_url.data
            #post.author = edit_form.author.data
            post.body = edit_form.body.data
            db.session.commit()
            return redirect(url_for("show_post", post_id=post.id))
    else:
        return render_template("make-post.html",
                               form=edit_form,
                               logged_in=current_user.is_authenticated)


@app.route("/delete/<int:post_id>")
@login_required
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


# Run the Application
if __name__ == "__main__":
    #app.run(host='0.0.0.0', port=5000)
    app.run(debug=True)
