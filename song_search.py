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
openai.api_key = "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"

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
        
    def searchForTrackURI(self, trackName):
        results = spotify.search(q=trackName, type='track', limit=1)
        items = results['tracks']['items']

        if len(items) > 0:
            trackURI = items[0]['uri']
            return trackURI
    
        else:
            print("No track URI available")
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
        return allArtistTracks

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

    def getRecommendedSongs(self, artistName, numSongs):
        recommendedSongs = []
    
        # Retrieve all songs by the artist
        recommendedArtistSongs = self.getArtistSongs(artistName)
    
        # Extract and return the name of the song, artist name, preview URL, song URI.
        for track in recommendedArtistSongs[:numSongs]:
            recommendedSongs.append({
            "name" : track['name'],
            "artist" : track['artists'][0]['name'],
            "preview_url": track['preview_url'], 
            "song_URI": track['uri']
        })

        return recommendedSongs
    
    def getSongDetails(self, trackName, artistName):
        results = spotify.search(q=trackName, type='track')
        items = results['tracks']['items']

        artist_results = spotify.search(q=artistName, type='artist')
        artist_items = results['artists']['items']

        songDetails = []

        if len(items) > 0:
            songDetails.append({
                "songName": items[0]['name'],
                "artistName": ", ".join(artist['name'] for artist in items[0]['artists']),  # Iterate over the list
                "albumName": items[0]['album']['name'],
                "releaseDate": items[0]['album']['release_date']
            })
        else:
            return None
        return songDetails
    
    def chat_with_GPT(self, prompt, numSongs):
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an assistant that recommends songs based on the game's title and genre. 
                    Get different artists for each song. Limit the total number of songs being recommended to { numSongs }"""
                },
                {
                    "role": "user",
                    "content": f"""Get recommended songs from different artists that match the vibe based on the given game title {prompt}. """
                }
            ],
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
