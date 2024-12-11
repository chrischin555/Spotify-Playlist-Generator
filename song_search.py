import json
from dotenv import load_dotenv
from requests import post, get
import os
import base64
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import openai

# Loads environment variables in the .env file.
load_dotenv()

client_id  = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = 'http://localhost:3000'
openai.api_key = "X"

scope = "streaming"

"""
Initializes the authorization end-point for authorizing a user's Spotify account.
"""
spotify_oauth = SpotifyOAuth(
    client_id = client_id,
    client_secret = client_secret,
    redirect_uri = redirect_uri,
    scope=scope,
    show_dialog = True
)

spotify = spotipy.Spotify(auth_manager=spotify_oauth)


class SpotifySongSearch: 
    """
    Class with the functions needed to utilize Spotify's API utilizing the Spotipy library.
    """
    def __init__(self):
        """
        Constructor to initialize an object to utilize the functions from the Spotipy library.
        """
        self.token = SpotifySongSearch.get_token()

    @staticmethod
    def get_token():
        """
        Obtains the user's Spotify token.
        """
        # Authorization string encoded in Base64; take client ID and concate to client secret & encode with Base64 to get Auth Token
        auth_string = client_id + ":" + client_secret
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

        url = "https://accounts.spotify.com/api/token"

        headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {"grant_type": "client_credentials"}
        result = post(url, headers=headers, data=data)
        json_result = json.loads(result.content)
        token = json_result["access_token"]
        return token

    def getAuthHeader(token):
        """
        Returns the authorization token.
        Args:
            token (String): the authorization token  
        """
        return {"Authorization": "Bearer " + token}

    def searchForArtist(self, artistName):
        """
        Searches for an artist's name.
        Args:
            artistName (String): the artist name
        Returns:
            String: The artist name.
        """
        results = spotify.search(q=artistName, type='artist')
        items = results['artists']['items']

        if len(items) > 0:
            artist = items[0]
            return artist['name']
    
        else:
            print("No artists with that name...")
            return None
        
    def searchForTrackURI(self, trackName):
        """
        Searches for the track's URI.
        Args:
            trackName (String): the track name
        Returns:
            String: The URI for the specified track.
        """
        results = spotify.search(q=trackName, type='track')
        items = results['tracks']['items']

        if len(items) > 0:
            trackURI = items[0]['uri']
            return trackURI
    
        else:
            print("No track URI available")
            return None
    
    def getArtistID(self, artistName):
        """
        Searches for ID associated with that artist.
        Args:
            artistName (String): the artist name
        Returns:
            String: The artist ID associated with that artist.
        """
        results = spotify.search(q=artistName, type='artist')
        items = results['artists']['items']

        if len(items) > 0:
            artist = items[0]
            return artist['id']
        else:
            print("No artists with that name...")
            return None

    def getArtistAlbums(self, artistName):
        """
        Searches for the artist's albums.
        Args:
            artistName (String): the artist name
        Returns:
            String: the name of the first album in the list of albums. 
        """
        artist_URI = f'spotify:artist:{self.getArtistID(artistName)}'

        results = spotify.artist_albums(artist_URI, album_type = 'single')
        albums = results['items']

        while results['next']:
            results = spotify.next(results)
            albums.extend(results['items'])

        for album in albums:
            return album['name']

    def getArtistAlbumID(self, artistName):
        """
        Retrieves the IDs for all the albums of an artist. 
        Args:
            artistName (String): the artist name
        Returns:
            list: a list of album IDs associated with that artist.
        """

        artist_URI = f'spotify:artist:{self.getArtistID(artistName)}'

        results = spotify.artist_albums(artist_URI, album_type = 'single')
        albums = results['items']
        albumIDs = []

        while results['next']:
            results = spotify.next(results)
            albums.extend(results['items'])

        for album in albums:
            albumIDs.append(album['id'])
        return albumIDs

    def getArtistSongs(self, artistName):
        """
        Retrieves all the songs of an artist.
        Args:
            artistName (String): the artist name
        Returns:
            list: a list of all the songs released by the artist.
        """

        allArtistAlbumIDs = self.getArtistAlbumID(artistName) # first get all the album IDs as the function takes only album IDs
        allArtistTracks = []

        for album_id in allArtistAlbumIDs:
            album_tracks = spotify.album_tracks(album_id)
            allArtistTracks.extend(album_tracks['items'])
     
        return allArtistTracks

    def getArtistSongIDs(self, artistName):
        """
        Retrieves all the song IDs associated with an artist.
        Args:
            artistName (String): the artist name
        Returns:
            list: a list of song IDs for that artist.
        """
        allArtistAlbumIDs = self.getArtistAlbumID(artistName)
        allArtistTrackIDs = []

        for album_id in allArtistAlbumIDs:
            album_tracks = spotify.album_tracks(album_id)
            allArtistTrackIDs.extend(track['id'] for track in album_tracks['items'])
        
        return allArtistTrackIDs

    def getRecommendedGenres():
        """
        Deprecated end point. Originally was going to be used for the recommend_songs endpoint.
        Before being deprecated, this function generated a seed of recommended genres.
        Returns:
            list: a list of recommended genres.
        """
        recommendations_seed = spotify.recommendation_genre_seeds()
        genresArray = recommendations_seed['genres']
        return genresArray

    def getRecommendedSongs(self, artistName, numSongs):
        """
        Generates recommended songs based on the artist name. The number of songs contained in the recommended songs list
        depends on the number of songs selected by the user.
        Args:
            artistName (String): the artist name
            numSongs (int): the number of songs
        Returns:
            dictionary: a dictionary containing each song by the artist, along with the name, artist, preview URL, song URI,
            and external URL.
        """
        recommendedSongs = []
    
        # Retrieve all songs by the artist
        recommendedArtistSongs = self.getArtistSongs(artistName)
    
        # Extract and return the name of the song, artist name, preview URL, song URI
        for track in recommendedArtistSongs[:numSongs]: # Limit entries to numSongs
            recommendedSongs.append({
            "name" : track['name'],
            "artist" : track['artists'][0]['name'],
            "preview_url": track['preview_url'], 
            "song_URI": track['uri'],
            "spotify_url": track['external_urls']['spotify']
        })

        return recommendedSongs
    
    def getSongDetails(self, songURI):
        """
        Retrieves a song's details based on the song's URI.
        Args:
            songURI (String): the song URI
        Returns:
            dictionary: the details of the song, which includes the artist name, song name, album name, and release date.
        """
        retrieveTrack = spotify.track(songURI)
        songDetails = []

        artistNames = ", ".join(artist['name'] for artist in retrieveTrack['artists'])
        
        songDetails = {
            "artistNames": artistNames,
            "songName": retrieveTrack['name'],
            "albumName": retrieveTrack['album']['name'],
            "releaseDate": retrieveTrack['album']['release_date']
        }

        return songDetails

    
    def chat_with_GPT(self, prompt, numSongs):
        """
        Utilizes OpenAI's GPT-4o to recommend songs based on the game's title and genre. The prompt (the game title) given to the function
        is from the front-end. The number of songs is selected by the user as well from the front end.
        Args:
            prompt (String): prompt given by the user
            numSongs (int): the number of songs
        Returns:
            object: the response message object from ChatGPT
        """
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an assistant that recommends songs based on the game's title and genre.
                    The number of songs are limited to { numSongs } in total. """
                },
                {
                    "role": "user",
                    "content": f"""Get recommended songs from different artists that match the vibe based on the given game title {prompt}. """
                }
            ],
            # Utilizes function-calling to format ChatGPT's response. This is done to make parsing the response easier,
            # allowing the user to grab the artistNames needed for the other functions.
            functions=[
                {
                    "name": "getRecommendedSongs",
                    "description": "Gets recommended songs based on the artist name and the genre.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "artistNames": {
                                "type": "array",
                                "description": "The name of the recommended artist to go off of. ",
                                "items": {
                                    "type": "string"
                                }
                            },
                            "numSongs": {
                                "type": "integer",
                                "description": "The total number of songs that will be recommended to the user."
                            }
                        },
                        "required": ["artistName"]
                    }
                }
            ],
            function_call = "auto"
        )
        # return response 
        return response.choices[0].message
