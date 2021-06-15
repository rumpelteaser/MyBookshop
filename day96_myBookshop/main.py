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
from forms import CreateBookForm, CreateRegisterForm, CreateLoginForm, CreateCommentForm
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
book_img = "https://images.unsplash.com/photo-1530482054429-cc491f61333b?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1651&q=80"
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
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookshop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Create DB Tables

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    # This will act like a list of Book objects attached to each User.
    # The "creator" refers to the 'creator' property in the Book class.
    books = relationship("Book", back_populates="creator")
    # This will act like a list of Comment objects attached to each User.
    # The "comment_creator" refers to the 'comment_creator' property in the Comment class.
    comments = relationship("Comment", back_populates="comment_creator")

class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    # Create Foreign Key, in "users.id" 'users' refers to the tablename of User.
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, "books" refers to the 'books' property in the User class.
    creator = relationship("User", back_populates="books")
    title = db.Column(db.String(250), unique=True, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    # This will act like a list of Comment objects attached to each Book.
    # The "parent_book" refers to the 'parent_book' property in the Comment class.
    comments = relationship("Comment", back_populates="parent_book")

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    # Create Foreign Key, in "users.id" 'users' refers to the tablename of User.
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, "comments" refers to the 'comments' property in the User class.
    comment_creator = relationship("User", back_populates="comments")
    # Create Foreign Key, in "books.id" 'books' refers to the tablename of Book.
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"))
    # Create reference to the Book object, "comments" refers to the 'comments' property in the User class.
    parent_book = relationship("Book", back_populates="comments")

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
def get_all_books():
    all_books = Book.query.all()
    return render_template("index.html",
                           books=all_books,
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
            return redirect(url_for('get_all_books'))
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
                return redirect(url_for('get_all_books'))
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
    return redirect(url_for('get_all_books'))


@app.route("/book/<int:book_id>", methods=["GET", "POST"])
def show_book(book_id):
    requested_book = Book.query.get(book_id)
    comment_form = CreateCommentForm()
    if request.method == "POST":
        if current_user.is_authenticated:
            new_comment = Comment(creator_id=current_user.id,
                                  book_id=requested_book.id,
                                  text=comment_form.comment_text.data)
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for('get_all_books'))
        else:
            flash("Sorry, you have to login to order books.")
            return redirect(url_for('login'))
    else:
        return render_template("book.html",
                               book=requested_book,
                               form=comment_form,
                               logged_in=current_user.is_authenticated,
                               comments=requested_book.comments)


@app.route("/about")
def about():
    return render_template("about.html", logged_in=current_user.is_authenticated)


@app.route("/contact")
def contact():
    return render_template("contact.html", logged_in=current_user.is_authenticated)


@app.route("/new-book", methods=["GET", "POST"])
@login_required
@admin_only
def add_new_book():
    book_form = CreateBookForm()
    if request.method == "POST":
        if book_form.validate_on_submit():
            print("Adding book")
            new_book = Book(
                title=book_form.title.data,
                author=book_form.author.data,
                body=book_form.body.data,
                #img_url=form.img_url.data,
                img_url=book_img,
                creator=current_user,
                date=date.today().strftime("%B %d, %Y")
                )
            print("book entry created")
            db.session.add(new_book)
            db.session.commit()
            print("book added")
            return redirect(url_for("get_all_books"))
        else:
            print("Form not validated")
            return redirect(url_for("get_all_books"))
    else:
        return render_template("insert-book.html",
                               form=book_form,
                               logged_in=current_user.is_authenticated)


@app.route("/edit-book/<int:book_id>", methods=["GET", "POST"])
@login_required
@admin_only
def edit_book(book_id):
    book = Book.query.get(book_id)
    edit_form = CreateBookForm(
        title=book.title,
        author=book.author,
        img_url=book.img_url,
        creator=book.creator,
        body=book.body
        )
    if request.method == "POST":
        if edit_form.validate_on_submit():
            book.title = edit_form.title.data
            book.author = edit_form.author.data
            book.img_url = edit_form.img_url.data
            #book.creator = edit_form.creator.data
            book.body = edit_form.body.data
            db.session.commit()
            return redirect(url_for("show_book", book_id=book.id))
    else:
        return render_template("insert-book.html",
                               form=edit_form,
                               logged_in=current_user.is_authenticated)


@app.route("/delete/<int:book_id>")
@login_required
@admin_only
def delete_book(book_id):
    book_to_delete = Book.query.get(book_id)
    db.session.delete(book_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_books'))


# Run the Application
if __name__ == "__main__":
    #app.run(host='0.0.0.0', port=5000)
    app.run(debug=True)
