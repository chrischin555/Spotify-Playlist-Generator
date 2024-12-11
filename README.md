# Spotify-Playlist-Generator

Game-Play is a Spotify playlist generator that utilizes Spotipy (a Python library that uses Spotify's Web API), OpenAI's API, and Python Steam API. Python Steam API is used to pull up a user's video game library on Steam. OpenAI's API was used to interact with GPT 4o to recommend songs based off a video game's genre (such as action, adventure, etc.).

Before getting started:
1) Make sure you have a Spotify account created. If you do not have a Spotify account created, the Spotify authorization end point will allow you to create a Spotify account.
2) Install the following libraries:
pip install flask, flask-sqlalchemy, flask-login, flask-wtf, wtforms, flask-bcrypt, spotipy, steam
Without the libraries installed above, the application cannot be run.


After installing the libraries, you are ready to run the application!
For command line users:
![image](https://github.com/user-attachments/assets/4d6e7e31-732d-4011-980d-9165e7834497). Afterward, go to localhost:5000, where the application will be hosted.

For IDE users, such as VSCode:
On the app.py file, click on "Run Python file." Afterward, go to localhost:5000, which is where the application will be hosted.
