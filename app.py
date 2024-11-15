import json
from flask import Flask, render_template, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired
from flask_bcrypt import Bcrypt
from song_search import SpotifySongSearch
from song_search_form import SongSearchForm
from recommend_songs import RecommendSongs
import openai

app = Flask(__name__)
# create database instance, connect app file to database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' 
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = "HjsX4l6X8dcJ7MHKOQaudZ4YD2yFTGwW" # secret key to establish cookie
bcrypt = Bcrypt(app)


# Allows our app and flask login to work together and handle things when logging in, loading in users, etc.
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Load user call back; used to reload user object from user id stored in the session
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# table for database with the three columns
# username, password have a max of 20 characters & 
# 80 characters respectively & cannot be null
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

# Registration Form, inherits from FlaskForm
class RegisterForm(FlaskForm):
    # Username field
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    # Password field; password is hashed
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    # Button to register
    submit = SubmitField("Register")

    # Queries database table by username and checks if there is a similar username entered. 
    # If there is one, raises validation error, stating the user already exists. 
    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username = username.data).first()
        if existing_user_username:
            raise ValidationError("Username already exists. Choose a different username.")

# Login Form, inherits from FlaskForm
class LoginForm(FlaskForm):
    # Username field
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    # Password field; password is hashed
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    # Button to register
    submit = SubmitField("Login")


    
# comment out after creating tables
# with app.app_context():
#     db.create_all()

@app.route('/') # render content in home after routing
def home():
    return render_template('home.html') # searches for file in template folder; in this case its home.html

@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Query user to check if they exist; checks if user is in database or not 
        user = User.query.filter_by(username=form.username.data).first()
        # If user exists, check the password hash; check user password and compare to form data.
        # Match = log in and redirect to dashboard.
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form) # Create form variable in HTML template

@app.route('/dashboard', methods = ['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout', methods = ['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegisterForm()

    # Whenever we submit the form, we immediately create a hashed version of the password. In other words, 
    # when we type in our password, it is hashed instead of encrypted. Once it's hashed, new user added to database.
    # Afterward, redirect to login page. 
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username = form.username.data, password = hashed_password)
        db.session.add(new_user)
        db.session.commit()
        print("added to database")
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

# test route, remove later because i just used this for testing
@app.route('/song_search', methods = ['GET', 'POST'])
def song_search():
    artistName = None
    form = SongSearchForm()
    songs = []

    # Validations
    if form.validate_on_submit():
        artistName = form.artistName.data
        form.artistName.data = ''
        song_search = SpotifySongSearch()
        songs = song_search.getArtistSongs(artistName)
    return render_template('song_search.html', artistName = artistName, form = form, songs = songs)

@app.route('/recommend_songs', methods = ['GET', 'POST'])
def recommend_songs():
    nameOfGame = None
    form = RecommendSongs()
    GPTResponse = None
    recommendedSongs = []
    numSongs = 0

    # Validations
    if form.validate_on_submit():
        nameOfGame = form.nameOfGame.data
        numSongs = form.numSongs.data
        form.nameOfGame.data = ''
        song_search = SpotifySongSearch()
        GPTResponse = song_search.chat_with_GPT(nameOfGame)
        artistName = json.loads(GPTResponse.function_call.arguments).get("artistName")
        genre = json.loads(GPTResponse.function_call.arguments).get("genre")
        recommendedSongs = song_search.getRecommendedSongs(artistName, genre, numSongs)
    return render_template('recommended_songs.html', nameOfGame = nameOfGame, 
                           form = form, GPTResponse = GPTResponse, recommendedSongs = recommendedSongs, numSongs = numSongs)

if __name__ == '__main__':
    app.run(debug=True)
    # spotify_search = SpotifySongSearch()
    # artist = spotify_search.searchForArtist("XG")
    # print(artist)
    # artistID = spotify_search.getArtistID(artist)
    # albums = spotify_search.getArtistAlbums(artist)
    # tracks = spotify_search.getArtistSongs(artist)


