import json
import re
import random

import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

with open("config.json") as f:
    config = json.load(f)

TOKEN = config["DISCORD_TOKEN"]
BOT_ID = config["DISCORD_BOT_ID"]
SPOTIFY_CLIENT_ID = config.get("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = config.get("SPOTIFY_CLIENT_SECRET", "")

bot = commands.Bot(
    command_prefix=None,
    help_command=None,
    is_case_insensitive=True,
    intents=discord.Intents.all(),
)

try:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    ))
except Exception:
    sp = None


def extract_spotify_id(url_or_id, content_type):
    if not url_or_id:
        return None
    
    patterns = {
        'playlist': r'playlist[/:]([a-zA-Z0-9]+)',
        'album': r'album[/:]([a-zA-Z0-9]+)',
        'track': r'track[/:]([a-zA-Z0-9]+)'
    }
    
    if content_type in patterns:
        match = re.search(patterns[content_type], url_or_id)
        if match:
            return match.group(1)
    
    if re.match(r'^[a-zA-Z0-9]+$', url_or_id):
        return url_or_id
    
    return None


def get_playlist_tracks(playlist_input):
    if not sp:
        return None, "Spotify API not configured"
    
    playlist_id = extract_spotify_id(playlist_input, 'playlist')
    if not playlist_id:
        return None, "Invalid playlist URL or ID format"
    
    try:
        results = sp.playlist_tracks(playlist_id)
        if not results or not results.get('items'):
            return None, "Playlist is empty or not found"
        
        tracks = []
        for item in results['items']:
            if item and item.get('track'):
                track = item['track']
                tracks.append({
                    'name': track.get('name', 'Unknown'),
                    'artist': track['artists'][0]['name'] if track.get('artists') else 'Unknown',
                    'id': track.get('id', '')
                })
        
        if not tracks:
            return None, "No valid tracks found in playlist"
        
        return tracks, None
    except spotipy.exceptions.SpotifyException:
        return None, "Playlist not found or is private"
    except Exception:
        return None, "Failed to fetch playlist data"


def get_album_tracks(album_input):
    if not sp:
        return None, "Spotify API not configured"
    
    album_id = extract_spotify_id(album_input, 'album')
    if not album_id:
        return None, "Invalid album URL or ID format"
    
    try:
        results = sp.album_tracks(album_id)
        if not results or not results.get('items'):
            return None, "Album is empty or not found"
        
        album_info = sp.album(album_id)
        artist_name = album_info['artists'][0]['name'] if album_info.get('artists') else 'Unknown'
        
        tracks = []
        for track in results['items']:
            tracks.append({
                'name': track.get('name', 'Unknown'),
                'artist': artist_name,
                'id': track.get('id', '')
            })
        
        if not tracks:
            return None, "No valid tracks found in album"
        
        return tracks, None
    except spotipy.exceptions.SpotifyException:
        return None, "Album not found or is private"
    except Exception:
        return None, "Failed to fetch album data"


def get_artist_top_tracks(artist_name):
    if not sp:
        return None, "Spotify API not configured"
    
    if not artist_name or len(artist_name.strip()) == 0:
        return None, "Artist name cannot be empty"
    
    try:
        results = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
        if not results or not results.get('artists') or not results['artists'].get('items'):
            return None, f"Artist '{artist_name}' not found"
        
        artist = results['artists']['items'][0]
        artist_id = artist['id']
        
        top_tracks = sp.artist_top_tracks(artist_id)
        if not top_tracks or not top_tracks.get('tracks'):
            return None, f"No tracks found for artist '{artist_name}'"
        
        tracks = []
        for track in top_tracks['tracks']:
            tracks.append({
                'name': track.get('name', 'Unknown'),
                'artist': artist['name'],
                'id': track.get('id', '')
            })
        
        if not tracks:
            return None, f"No valid tracks found for artist '{artist_name}'"
        
        return tracks, None
    except spotipy.exceptions.SpotifyException:
        return None, f"Failed to search for artist '{artist_name}'"
    except Exception:
        return None, "Failed to fetch artist data"


@bot.event
async def on_ready():
    print("Ready!")
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} commands")


@bot.tree.command(
    name="guess",
    description="Guess the song from the lyrics. Requires spotify oauth connection.",
)
async def guess(
    interaction: discord.Interaction,
    source_type: str = "playlist",
    source_input: str = ""
):
    if not sp:
        await interaction.response.send_message(
            "Spotify API is not configured. Please add credentials to config.json",
            ephemeral=True
        )
        return
    
    if not source_input:
        await interaction.response.send_message(
            "Please provide a playlist URL, album URL, or artist name",
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    tracks = None
    error_msg = None
    
    if source_type.lower() == "playlist":
        tracks, error_msg = get_playlist_tracks(source_input)
    elif source_type.lower() == "album":
        tracks, error_msg = get_album_tracks(source_input)
    elif source_type.lower() == "artist":
        tracks, error_msg = get_artist_top_tracks(source_input)
    else:
        error_msg = "Invalid source type. Use 'playlist', 'album', or 'artist'"
    
    if error_msg:
        await interaction.followup.send(
            f"Error: {error_msg}\nPlease check your input and try again.",
            ephemeral=True
        )
        return
    
    if not tracks:
        await interaction.followup.send(
            "No tracks found. Please try again with a different source.",
            ephemeral=True
        )
        return
    
    selected_track = random.choice(tracks)
    await interaction.followup.send(
        f"Game started! Guess the song:\n**Artist:** {selected_track['artist']}\n**Track:** {selected_track['name']}"
    )


bot.run(TOKEN)
