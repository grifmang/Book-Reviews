import os
import json
import re
import xml.etree.ElementTree as ET
import oauth2 as oauth
import requests
from flask import Flask, jsonify, session, flash, url_for, redirect, render_template, request, g
from flask_session import Session
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
DATABASE_URL = os.environ['DATABASE_URL']

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# API and OAuth Config
api_key = os.getenv("API_KEY")
consumer = oauth.Consumer(key=api_key,
                          secret=os.getenv("SECRET"))
token = oauth.Token(os.getenv("CONSUMER"),
                    os.getenv("OAUTH_SECRET"))
client = oauth.Client(consumer, token)

@app.route("/")
@app.route('/index')
def index():
    return render_template("books.html")

@app.route("/error")
def error():
    return render_template("404.html")

@app.route("/books", methods=["GET"])
def books():

    return render_template("books.html")

@app.route("/api/<string:isbn>", methods=["GET"])
def api(isbn):
    gr_api = "https://www.goodreads.com/book/isbn/"
    response = requests.get(gr_api+isbn+'?key='+api_key)
    response_xml = ET.fromstring(response.content)
    avg_rating = response_xml.find('book').find('average_rating').text
    reviews_count = response_xml.find('book').find('work').find('reviews_count').text
    book_data = db.execute("SELECT * FROM books WHERE books.isbn = :isbn", {"isbn": isbn}).first()
    results = dict(title= book_data[1],
                   author= book_data[2],
                   year= book_data[3],
                   isbn= isbn,
                   review_count= reviews_count,
                   average_score= avg_rating)
    return jsonify(results)

@app.route("/details/<string:isbn_number>", methods=["GET"])
def details(isbn_number):

    book_data = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn_number}).first()
    review_data = db.execute("SELECT users.username, reviews.review FROM users JOIN reviews ON reviews.user_id=users.id JOIN books ON reviews.book_id=books.isbn WHERE books.isbn=:book_id", {"book_id":isbn_number}).fetchall()
    gr_api = "https://www.goodreads.com/book/isbn/"
    response = requests.get(gr_api+isbn_number+'?key='+api_key)
    response_xml = ET.fromstring(response.content)
    small_image_url = response_xml.find('book').find('image_url').text
    description = response_xml.find('book').find('description').text
    avg_rating = response_xml.find('book').find('average_rating').text
    ratings_count = response_xml.find('book').find('work').find('ratings_count').text

    def remove_html_tags(text):
        """Remove html tags from a string"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    description = remove_html_tags(description)

    return render_template("details.html", isbn=isbn_number, title=book_data[1],
                            author=book_data[2], year=book_data[3], review_data=review_data,
                            description=description, small_image=small_image_url,
                            average_rating=avg_rating, ratings_count=ratings_count)

@app.route("/post/<string:isbn_number>", methods=["GET", "POST"])
def post(isbn_number):

    try:
        if session['user_id']:

            if request.method == "POST":
                title = db.execute("SELECT title from books where isbn = :book_id", {"book_id": isbn_number}).first()[0]
                star_one = request.form.get('star-1')
                content = request.form.get('content')
                star_two = request.form.get('star-2')
                star_three = request.form.get('star-3')
                star_four = request.form.get('star-4')
                star_five = request.form.get('star-5')
                if star_one:
                    rating = 1
                elif star_two:
                    rating = 2
                elif star_three:
                    rating = 3
                elif star_four:
                    rating = 4
                else:
                    rating = 5

                user_id = db.execute("SELECT id FROM users WHERE username = :user_id", {"user_id": session["user_id"]}).first()[0]
                db.execute("INSERT INTO reviews (review, book_id, user_id, rating) VALUES (:review, :book_id, :user_id, :rating)",
                            {"review": content, "user_id": user_id, "rating": rating, "book_id": isbn_number})
                flash("Thanks for the review!")
                db.commit()
                return render_template("post.html", title=title, isbn_number=isbn_number)
            else:
                title = db.execute("SELECT title from books where isbn = :book_id", {"book_id": isbn_number}).first()[0]
                return render_template("post.html", title=title, isbn_number=isbn_number)

    except KeyError:
        flash("Please login to leave a review.")
        return redirect(url_for('login'))


@app.route("/search", methods=["POST"])
def search():
    if request.method == "POST":

        nums = db.execute("SELECT * from books").fetchall()

        if request.form.get("isbn"):
            result = []
            isbn_form = request.form.get("isbn")
            for num in nums:
                if isbn_form in num[0]:
                    result.append([num[0], num[1], num[2], num[3]])
            if len(result) == 0:
                return redirect(url_for('error'))
            else:
                return render_template("search.html", result=result)

        elif request.form.get("title"):
            result = []
            title_form = request.form.get("title").lower()
            title_form = title_form.strip(',')
            title_form = title_form.strip('.')
            for num in nums:
                if title_form in num[1].lower():
                    result.append([num[0], num[1], num[2], num[3]])
            return render_template("search.html", result=result)

        elif request.form.get("author"):
            result = []
            author_form = request.form.get("author").lower()
            author_form = author_form.strip(',')
            author_form = author_form.strip('.')
            for num in nums:
                if author_form in num[2]:
                    result.append([num[0], num[1], num[2], num[3]])
            return render_template("search.html", result=result)
        else:
            flash("You must enter search criteria.")
            return render_template('books.html')

@app.route("/change", methods=["GET", "POST"])
def change():

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        new_one = request.form.get("new_password")
        new_two = request.form.get("new_password2")

        e_hash = db.execute("SELECT hash FROM users WHERE username = :id", {"id": session["user_id"]}).first()
        user_pass = str(e_hash["hash"])

        if not request.form.get("current_password"):
            flash("Must enter current password!")
            return redirect(url_for("change"))
        elif not request.form.get("new_password") or not request.form.get("new_password2"):
            flash("Please enter new password.")
            return redirect(url_for("change"))
        elif not pwd_context.verify(request.form.get("current_password"), user_pass):
            flash("Current password does not match.")
            return redirect(url_for("change"))
        else:
            if new_one != new_two:
                flash("New passwords must match.")
                return redirect(url_for("change"))
            else:
                db.execute("UPDATE users SET hash = :hash WHERE username = :id", {"hash": pwd_context.encrypt(request.form.get("new_password")), "id": session["user_id"]})
                db.commit()
                flash("Password Successfully Reset!")
                return render_template("change.html")

    return render_template("change.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return "Must provide username"

        # ensure password was submitted
        elif not request.form.get("password"):
            return "Must provide password"

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :user", {"user": request.form.get("username")}).fetchall()

        # ensure username exists and password is correct
        if not rows or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            flash("Invalid username and/or password")
            return redirect(url_for("login"))


        # remember which user has logged in
        session["user_id"] = rows[0]["username"]

        # redirect user to home page
        flash("Logged In!")
        return redirect(url_for("books"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    """Register user."""
    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            flash('Must provide username. Please try again!')
            return redirect(url_for("register"))

        # ensure password was submitted
        if not request.form.get("password"):
            error = "Must provide password."
            return redirect(url_for("register"))

        elif not request.form.get("password2") or request.form.get("password") != request.form.get("password2"):
            error = "Passwords don't match."
            return redirect(url_for("register"))

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :user", {"user": request.form.get("username")}).first()

        # ensure username exists
        if rows:
            error = "Username in use. Please choose another"
            return redirect(url_for("register"))

        #Insert user information in to database
        db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", {"username": request.form.get("username"), "hash": pwd_context.encrypt(request.form.get("password"))})

        #Query db for new user
        newRows = db.execute("SELECT * FROM users WHERE username = :username", {"username": request.form.get("username")}).fetchall()

        #login new user
        session["user_id"] = newRows[0]["username"]

        #redirect to home page
        db.commit()
        flash("Registered!")
        return redirect(url_for("index"))

    return render_template("register.html")

if __name__ == '__main__':
    app.run()
