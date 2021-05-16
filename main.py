from os.path import abspath
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, validators, FloatField
from wtforms.validators import DataRequired
import requests
import os

URL_SEARCH_END_POINT = "https://api.themoviedb.org/3/search/movie"
URL_FIND_END_POINT = "https://api.themoviedb.org/3/movie"
MOVIE_DATABASE_API = os.getenv('MOVIE_DATABASE_API')
IMAGE_URL = "https://image.tmdb.org/t/p/w500"
current_path = abspath(f"{os.getcwd()}/movies.db")

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{current_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Bootstrap(app)
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    year = db.Column(db.String)
    description = db.Column(db.String)
    rating = db.Column(db.Float)
    ranking = db.Column(db.String)
    review = db.Column(db.String)
    img_url = db.Column(db.String)

    def __repr__(self):
        return '<Movie %r>' % self.title


db.create_all()


class UpdateForm(FlaskForm):
    new_rating = FloatField('Your Rating Out of 10 e.g. 7.7')
    new_review = StringField(u'Your Review')
    submit_btn = SubmitField(u'Done')


class AddForm(FlaskForm):
    new_title = StringField('Movie Title')
    submit_btn = SubmitField(u'Add Movie')


@app.route("/")
def home():
    movies = Movie.query.order_by(Movie.rating).all()
    for movie in movies:
        movie.ranking = movies.index(movie) + 1
        db.session.commit()
    return render_template("index.html", movies=movies)


@app.route("/update/<movie_id>", methods=['POST', 'GET'])
def update(movie_id):
    form = UpdateForm()
    if request.method == 'POST':
        movie = Movie.query.get(movie_id)
        if form.new_rating.data:
            movie.rating = form.new_rating.data
        if form.new_review.data:
            movie.review = form.new_review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie_id=movie_id, form=form)


@app.route("/delete/<movie_id>")
def delete(movie_id):
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["POST", "GET"])
def add():
    form = AddForm()
    if request.method == "POST":
        params = {
            'api_key': MOVIE_DATABASE_API,
            'query': form.new_title.data,
            'language': 'en-US'
        }
        movies_data = requests.get(url=URL_SEARCH_END_POINT, params=params).json().get('results')
        return render_template('select.html', movies=movies_data)
    return render_template("add.html", form=form)


@app.route('/select/<int:movie_id>')
def select(movie_id):
    params = {
        'api_key': MOVIE_DATABASE_API,
    }
    movie = requests.get(url=f"{URL_FIND_END_POINT}/{movie_id}", params=params).json()
    print(movie)
    title = movie.get("original_title")
    year = movie.get("release_date")
    description = movie.get("overview")
    rating = movie.get("vote_average")
    review = "I like it"
    img_url = f"{IMAGE_URL}{movie.get('poster_path')}"
    movie_selected = Movie(title=title,
                           year=year.split("-")[0],
                           description=description,
                           rating=rating,
                           ranking="",
                           review=review,
                           img_url=img_url)
    db.session.add(movie_selected)
    db.session.commit()
    return redirect(url_for('update', movie_id=movie_selected.id))


if __name__ == '__main__':
    app.run(debug=True)
