import json
from dotenv import load_dotenv
from requests import post, get
import os
import base64
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import openai


load_dotenv()

client_id  = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = 'http://localhost:3000'
openai.api_key = "X"

scope = "streaming"

spotify_oauth = SpotifyOAuth(
    client_id = client_id,
    client_secret = client_secret,
    redirect_uri = redirect_uri,
    scope=scope,
    show_dialog = True
)

spotify = spotipy.Spotify(auth_manager=spotify_oauth)

# print(client_id)
# print(client_secret)
class SpotifySongSearch: 

    def __init__(self):
        self.token = SpotifySongSearch.get_token()

    @staticmethod
    def get_token():
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
        return {"Authorization": "Bearer " + token}

    def searchForArtist(self, artistName):
        results = spotify.search(q=artistName, type='artist')
        items = results['artists']['items']

        if len(items) > 0:
            artist = items[0]
            return artist['name']
    
        else:
            print("No artists with that name...")
            return None
    
    def getArtistID(self, artistName):
        results = spotify.search(q=artistName, type='artist')
        items = results['artists']['items']

        if len(items) > 0:
            artist = items[0]
            return artist['id']
        else:
            print("No artists with that name...")
            return None

    def getArtistAlbums(self, artistName):
        artist_URI = f'spotify:artist:{self.getArtistID(artistName)}'

        results = spotify.artist_albums(artist_URI, album_type = 'single')
        albums = results['items']

        while results['next']:
            results = spotify.next(results)
            albums.extend(results['items'])

        for album in albums:
            return album['name']

    def getArtistAlbumID(self, artistName):
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
        allArtistAlbumIDs = self.getArtistAlbumID(artistName)
        allArtistTracks = []

        for album_id in allArtistAlbumIDs:
            album_tracks = spotify.album_tracks(album_id)
            allArtistTracks.extend(album_tracks['items'])
    
        # for track in allArtistTracks:
        #     print('Track: ' + track['name']) 
        return [track['name'] for track in allArtistTracks]

    def getArtistSongIDs(self, artistName):
        allArtistAlbumIDs = self.getArtistAlbumID(artistName)
        allArtistTrackIDs = []

        for album_id in allArtistAlbumIDs:
            album_tracks = spotify.album_tracks(album_id)
            allArtistTrackIDs.extend(track['id'] for track in album_tracks['items'])
            
        # for trackID in allArtistTrackIDs:
        #     print('Track ID: ', trackID)
            
        return allArtistTrackIDs

    def getRecommendedGenres():
        recommendations_seed = spotify.recommendation_genre_seeds()
        genresArray = recommendations_seed['genres']
        return genresArray

    def getRecommendedSongs(self, artistName, genre, numSongs):
        recommended = []
        recommendedSongs = []
        recommendedArtist = self.getArtistID(artistName)
        recommendedArtistSongIDs = self.getArtistSongIDs(artistName)[:2]

        recommendedGenre = genre[:2]

        recommendations = spotify.recommendations([recommendedArtist], [recommendedGenre], recommendedArtistSongIDs, limit = numSongs)
        recommended.extend(recommendations['tracks'])

        for track in recommendations['tracks']:
            recommendedSongs.append({
                "name": track['name'],
                "artist": track['artists'][0]['name'],
                "preview_url": track['preview_url']
            })

        return recommendedSongs
    
    def chat_with_GPT(self, prompt):
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that recommends songs based on the game's title and genre."
                },
                {
                    "role": "user",
                    "content": f"Get recommended songs from different artists that match the vibe based on the given game title {prompt}. Limit the song genre to one and format it in lower case."
                }
            ],
            functions=[
                {
                    "name": "getRecommendedSongs",
                    "description": "Gets recommended songs based on the artist name and the genre.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "artistName": {
                                "type": "string",
                                "description": "The name of the recommended arist to go off of. ",
                            },
                            "genre": {
                                "type": "string",
                                "description": "The genre of the recommended arist to go off of.",
                            },
                        },
                        "required": ["artistName", "genre"],
                    }
                }
            ],
            function_call = "auto"
        )
        # return response 
        return response.choices[0].message
