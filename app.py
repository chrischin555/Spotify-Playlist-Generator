import json
import openai
from flask import Flask, render_template, url_for, redirect, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired
from flask_bcrypt import Bcrypt
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
from song_search import SpotifySongSearch
from song_search_form import SongSearchForm
from recommend_songs import RecommendSongs

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

#Spotipy variables, spotify dev info + sp_oauth
client_id = '0985d3da19014f2588b78ccd7d172db0'
client_secret = 'a73d7992813e4ffab54fc1b719944dca'
redirect_uri = 'http://localhost:5000/callback'
scope = 'playlist-read-private, playlist-modify-public, playlist-modify-private'

cache_handler = FlaskSessionCacheHandler(session)

sp_oauth = SpotifyOAuth( 
    client_id = client_id,
    client_secret = client_secret,
    redirect_uri = redirect_uri,
    scope = scope,
    cache_handler = cache_handler,
    show_dialog = True
)

sp = Spotify(auth_manager = sp_oauth)

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
    
#New Play List Form, from FlaskForm
class NewPlaylist(FlaskForm):
    name = StringField('Playlist Name', validators=[DataRequired()])  # Renamed to 'name'
    public_check = BooleanField('Public?')
    description = TextAreaField('Description')
    submit = SubmitField('Create Playlist')

    
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
    return render_template('login.html', form=form) # Create form variable in HTML template

@app.route('/dashboard', methods = ['GET', 'POST'])
@login_required
def dashboard():
    #For logging into Spotify
    if not sp_oauth.validate_token(cache_handler.get_cached_token()): #if not logged in in spotify
        auth_url = sp_oauth.get_authorize_url() #sign in through spotify
        return redirect(auth_url)
    return render_template('dashboard.html')

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

#spotify token refresh
@app.route('/callback')
def callback():
    sp_oauth.get_access_token(request.args['code']) #refreshes the spotify token (?)
    return redirect(url_for('dashboard'))

#spotipy access playlists
@app.route('/get_playlists')
def get_playlists():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()): # if not logged in in Spotify
        auth_url = sp_oauth.get_authorized_url() # sign in through Spotify
        return redirect(auth_url)

    playlists = sp.current_user_playlists()
    playlists_info = [(pl['name'], pl['external_urls']['spotify']) for pl in playlists['items']]
    playlists_html = '<br>'.join(f'{name}: <a href="{url}" target="_blank">{url}</a>' for name, url in playlists_info)
    
    create_playlist_button = '<br><br><a href="' + url_for('create_playlist') + '"><button>Create A New Playlist</button></a>'
    return playlists_html + create_playlist_button


@app.route('/create_playlists', methods=['GET', 'POST'])
def create_playlist():
    # Check if user is authenticated with Spotify
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()  # Redirect to Spotify login
        return redirect(auth_url)
    
    form = NewPlaylist()
    # If form is submitted and valid, process playlist creation
    if form.validate_on_submit():
        user_id = sp.current_user()['id']
        playlist_name = form.name.data
        playlist_public = form.public_check.data
        playlist_description = form.description.data
        
        # Create playlist
        new_list = sp.user_playlist_create(
            user = user_id, 
            name = playlist_name, 
            public = playlist_public, 
            collaborative = False, 
            description = playlist_description
        )

        flash('New playlist created successfully!', 'success')
        return redirect(url_for('get_playlists'))
    
    return render_template('new_playlist.html', form=form)

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
    songPreviews = None

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
        songPreviews = [song['preview_url'] for song in recommendedSongs if song['preview_url']]
    return render_template('recommended_songs.html', nameOfGame = nameOfGame, 
                           form = form, GPTResponse = GPTResponse, recommendedSongs = recommendedSongs, 
                           numSongs = numSongs, songPreviews = songPreviews)

@app.route('/logout', methods = ['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)


