import json
import os
from flask import Flask, render_template, url_for, redirect, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
import urllib
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired
from flask_bcrypt import Bcrypt
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
from recommend_songs import RecommendSongs
from song_search import SpotifySongSearch
from steam_web_api import Steam
from steam_owned_games import fetch_games

app = Flask(__name__)
# create database instance, connect app file to database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' 
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = "X" # secret key to establish cookie
bcrypt = Bcrypt(app)

# Allows our app and flask login to work together and handle things when logging in, loading in users, etc.
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

#Spotipy variables, spotify dev info + sp_oauth
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
KEY = os.getenv("STEAM_API_KEY")
steam = Steam(KEY)
steam_ID = "76561198108372769"
stored_steam_ID = None
gameNames = []

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



# table for database with the four columns
# username, password have a max of 20 characters & 
# 80 characters respectively & cannot be null
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

#table for database with song name and the URI
class Songs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    song_name = db.Column(db.String(80), nullable=False)
    song_URI = db.Column(db.String(80), nullable=False)

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
    # db.create_all()
    # db.drop_all()

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
                session.clear()
                login_user(user)
                #For logging into Spotify
                if not sp_oauth.validate_token(cache_handler.get_cached_token()): #if not logged in in spotify
                    auth_url = sp_oauth.get_authorize_url() #sign in through spotify
                    return redirect(auth_url)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form) # Create form variable in HTML template

@app.route('/dashboard', methods = ['GET', 'POST'])
@login_required
def dashboard():
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

# account information
@app.route('/account', methods = ['GET', 'POST'])
@login_required
def account():
    global stored_steam_ID
    global gameNames
    # Check if the Spotify token is valid
    if sp_oauth.validate_token(cache_handler.get_cached_token()):
        # If valid, set isSpotifyConnected to True
        isSpotifyConnected = True

    else:
        # If not valid, set isSpotifyConnected to False
        isSpotifyConnected = False
    
    if request.method == 'POST':
        stored_steam_ID = request.form.get("steam_id")
        if stored_steam_ID:
            session['steam_id'] = stored_steam_ID  # Save to session
            flash(f"Steam ID {stored_steam_ID} has been saved!", "success")
        else:
            flash("Please enter a valid Steam ID.", "warning")

        # Retrieve Steam ID from session if it exists
        steam_id = session.get('steam_id')

        print("steam ID:", steam_id)

    return render_template('account.html', current_user = current_user, isSpotifyConnected = isSpotifyConnected, steam_id = stored_steam_ID)

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

#spotipy access playlists
@app.route('/your_playlists', methods = ['GET', 'POST'])
@login_required
def get_playlists():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)

    playlists = sp.current_user_playlists()

    playlists_info = [
        (
            pl['name'], 
            pl['external_urls']['spotify'] if pl and isinstance(pl, dict) and 'external_urls' in pl and 'spotify' in pl['external_urls'] else 'No URL'
        )
        for pl in playlists.get('items', [])
        if pl is not None
    ]

    return render_template('playlists.html', playlists=playlists_info)


@app.route('/create_playlists', methods=['GET', 'POST'])
@login_required
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

@app.route('/add_to_playlist', methods=['POST'])
@login_required
def add_to_playlist():
    playlist_id = request.form.get('playlist_id') 
    song_urls = request.form.getlist('song_URIs')  # Correct key name
    # song_URIs = []
    print(f"Form Data Received: {request.form}")
    print(f"Playlist ID: {playlist_id}")
    print(f"Song URL: {song_urls}")

    if playlist_id and song_urls:
        song_URIs = [
            url.replace("https://open.spotify.com/track/", "spotify:track:").split("?")[0]
            for url in song_urls
        ]
        print(f"Transformed Song URIs: {song_URIs}")

        try:
            sp.playlist_add_items(playlist_id, song_URIs)
            flash("Successfully added songs to the playlist!", 'success')
        except Exception as e:
            print(f"Error Adding Songs: {e}")
            flash("Error occurred while adding songs to the playlist.", 'danger')
    else:
        if not playlist_id:
            flash("No playlist selected!", 'warning')
        if not song_urls:
            flash("No songs selected!", 'warning')

    return redirect(url_for('recommend_songs'))


@app.route('/logout', methods = ['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/recommend_songs', methods = ['GET', 'POST'])
@login_required
def recommend_songs():
    nameOfGame = None
    form = RecommendSongs()
    GPTResponse = None
    global recommendedSongs
    recommendedSongs = []
    numSongs = 0
    songPreviews = None
    global song_name
    global song_URI
    # song_URI = None
    # global artistName
    playlists_info = []

    steam_ID = session.get('steam_id')
    if(steam_ID):
        games = fetch_games(steam_ID)
        for app_id, details in games.items():
            print(f"App ID: {app_id}, Name: {details['Name']}, Playtime: {details['Playtime (Minutes)']} minutes")
            gameNames.append(details['Name'])
    
    form.nameOfGame.choices = gameNames

    for names in gameNames:
            print("names: " + names)

    # Validations
    if form.validate_on_submit():
         # To get playlists again
        if not sp_oauth.validate_token(cache_handler.get_cached_token()):  # if not logged in in Spotify
            auth_url = sp_oauth.get_authorize_url()  # sign in through Spotify
            return redirect(auth_url)
        
        numSongs = form.numSongs.data
        nameOfGame = form.nameOfGame.data
        form.nameOfGame.data = ''
        song_search = SpotifySongSearch()
        GPTResponse = song_search.chat_with_GPT(nameOfGame, numSongs)
        artistNames = json.loads(GPTResponse.function_call.arguments).get("artistNames", [])

        # Get user playlists
        playlists = sp.current_user_playlists()
        playlists_info = [
            (
                pl['name'], 
                pl['external_urls']['spotify'] if pl and isinstance(pl, dict) and 'external_urls' in pl and 'spotify' in pl['external_urls'] else 'No URL'
            )
            for pl in playlists.get('items', [])
            if pl is not None
        ]

        for artist in artistNames:
            recommendedSongs += song_search.getRecommendedSongs(artist, numSongs)

        songPreviews = [song['preview_url'] for song in recommendedSongs if song['preview_url']]
        
        # Clear table before adding new songs
        db.session.query(Songs).delete()
        db.session.commit()

        for song in recommendedSongs:
            song_name = song['name']
            song_URI = song['song_URI']
            artistName = song['artist']
            songURL = song['spotify_url']
            print("song name:", song_name)
            print("song URI:", song_URI)
            print("artist: ", artistName)
            print("song url: ", songURL)
            recommendedSong = Songs(song_name = song_name, song_URI = song_URI)
            db.session.add(recommendedSong)
            db.session.commit()
        
    return render_template('recommended_songs.html', nameOfGame = nameOfGame, 
                           form = form, GPTResponse = GPTResponse, recommendedSongs = recommendedSongs,
                           numSongs = numSongs, songPreviews = songPreviews, playlists = playlists_info)

@app.route('/songs/')
@login_required
def song_details():
    recommendedSongs = []
    song_search = SpotifySongSearch()
    song_URI = request.args.get('song_URI')

    # song = Songs.query.filter_by(song_name = song_name).first()

    if not song_URI:
        flash("Song not found in the database.", "danger")
        return redirect(url_for('recommended_songs'))
    
    decodedSongURI = urllib.parse.unquote(song_URI)
    songDetails = song_search.getSongDetails(decodedSongURI)

    for song in songDetails:
        print(song)
    
    return render_template('recommended_song_details.html', song_URI = song_URI, songDetails = songDetails, recommendedSongs = recommendedSongs)

if __name__ == '__main__':
    song_search = SpotifySongSearch()
    # testURI = song_search.searchForTrackURI("Enemy with JID (Opening Title Version) (from the series Arcane League of Legends)")
    # print(song_search.getRecommendedSongs("BLACKPINK"))
    # print(song_search.chat_with_GPT("League of Legends", 1))
    # print(song_search.getSongDetails(testURI))
    app.run(debug=True)
    # games = fetch_games(steam_ID)

    # gameNames = []
    # for app_id, details in games.items():
    #     print(f"App ID: {app_id}, Name: {details['Name']}, Playtime: {details['Playtime (Minutes)']} minutes")
    #     gameNames.append(details['Name'])
    # print("\n\n\n\n")

    # for names in gameNames:
    #     print("names: " + names)


  
