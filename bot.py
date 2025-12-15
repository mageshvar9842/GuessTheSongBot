import json
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any
import discord
from discord.ext import commands

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(f'bot_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

# Create logger instances
logger = logging.getLogger('DiscordBot')
spotify_logger = logging.getLogger('SpotifyAPI')
oauth_logger = logging.getLogger('OAuth')

# Set specific log levels if needed
spotify_logger.setLevel(logging.DEBUG)
oauth_logger.setLevel(logging.DEBUG)

try:
    with open("config.json") as f:
        config = json.load(f)
    logger.info("Configuration file loaded successfully")
except FileNotFoundError:
    logger.critical("config.json not found!")
    raise
except json.JSONDecodeError as e:
    logger.critical(f"Failed to parse config.json: {e}")
    raise

TOKEN = config["DISCORD_TOKEN"]
BOT_ID = config["DISCORD_BOT_ID"]

bot = commands.Bot(
    command_prefix=None,
    help_command=None,
    is_case_insensitive=True,
    intents=discord.Intents.all(),
)

class SpotifyInputValidator:
    """Validates Spotify URLs and IDs"""
    
    PLAYLIST_URL_PATTERN = re.compile(
        r'https?://open\.spotify\.com/playlist/([a-zA-Z0-9]+)(\?.*)?'
    )
    ALBUM_URL_PATTERN = re.compile(
        r'https?://open\.spotify\.com/album/([a-zA-Z0-9]+)(\?.*)?'
    )
    ARTIST_URL_PATTERN = re.compile(
        r'https?://open\.spotify\.com/artist/([a-zA-Z0-9]+)(\?.*)?'
    )
    TRACK_URL_PATTERN = re.compile(
        r'https?://open\.spotify\.com/track/([a-zA-Z0-9]+)(\?.*)?'
    )
    
    # Spotify IDs are 22 characters (base62 encoded)
    ID_PATTERN = re.compile(r'^[a-zA-Z0-9]{22}$')
    
    @staticmethod
    def extract_playlist_id(input_str: str) -> Optional[str]:
        """Extract playlist ID from URL or validate direct ID"""
        if not input_str:
            return None
            
        input_str = input_str.strip()
        
        # Check if it's a URL
        match = SpotifyInputValidator.PLAYLIST_URL_PATTERN.match(input_str)
        if match:
            return match.group(1)
        
        # Check if it's a direct ID
        if SpotifyInputValidator.ID_PATTERN.match(input_str):
            return input_str
        
        return None
    
    @staticmethod
    def extract_album_id(input_str: str) -> Optional[str]:
        """Extract album ID from URL or validate direct ID"""
        if not input_str:
            return None
            
        input_str = input_str.strip()
        
        # Check if it's a URL
        match = SpotifyInputValidator.ALBUM_URL_PATTERN.match(input_str)
        if match:
            return match.group(1)
        
        # Check if it's a direct ID
        if SpotifyInputValidator.ID_PATTERN.match(input_str):
            return input_str
        
        return None
    
    @staticmethod
    def extract_artist_id(input_str: str) -> Optional[str]:
        """Extract artist ID from URL or validate direct ID"""
        if not input_str:
            return None
            
        input_str = input_str.strip()
        
        # Check if it's a URL
        match = SpotifyInputValidator.ARTIST_URL_PATTERN.match(input_str)
        if match:
            return match.group(1)
        
        # Check if it's a direct ID
        if SpotifyInputValidator.ID_PATTERN.match(input_str):
            return input_str
        
        return None
    
    @staticmethod
    def validate_artist_name(name: str) -> bool:
        """Validate artist name (basic check)"""
        if not name or not name.strip():
            return False
        # Artist names should be between 1 and 100 characters
        name = name.strip()
        return 1 <= len(name) <= 100

class ErrorMessages:
    """Centralized error messages for better UX"""
    
    INVALID_PLAYLIST = (
        "❌ **Invalid Playlist**\n"
        "The playlist URL or ID you provided is invalid.\n\n"
        "**Valid formats:**\n"
        "• Playlist URL: `https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M`\n"
        "• Playlist ID: `37i9dQZF1DXcBWIGoYBM5M`\n\n"
        "Please try again with a valid playlist."
    )
    
    INVALID_ALBUM = (
        "❌ **Invalid Album**\n"
        "The album URL or ID you provided is invalid.\n\n"
        "**Valid formats:**\n"
        "• Album URL: `https://open.spotify.com/album/6DEjYFkNZh67HP7R9PSZvv`\n"
        "• Album ID: `6DEjYFkNZh67HP7R9PSZvv`\n\n"
        "Please try again with a valid album."
    )
    
    INVALID_ARTIST = (
        "❌ **Invalid Artist**\n"
        "The artist URL, ID, or name you provided is invalid.\n\n"
        "**Valid formats:**\n"
        "• Artist URL: `https://open.spotify.com/artist/0TnOYISbd1XYRBk9myaseg`\n"
        "• Artist ID: `0TnOYISbd1XYRBk9myaseg`\n"
        "• Artist name: `Pitbull`\n\n"
        "Please try again with a valid artist."
    )
    
    PLAYLIST_NOT_FOUND = (
        "❌ **Playlist Not Found**\n"
        "The playlist could not be found on Spotify. It may be:\n"
        "• Private or deleted\n"
        "• Restricted in your region\n"
        "• Temporarily unavailable\n\n"
        "Please check the playlist and try again."
    )
    
    ALBUM_NOT_FOUND = (
        "❌ **Album Not Found**\n"
        "The album could not be found on Spotify. It may be:\n"
        "• Removed or unavailable\n"
        "• Restricted in your region\n"
        "• Temporarily unavailable\n\n"
        "Please check the album and try again."
    )
    
    ARTIST_NOT_FOUND = (
        "❌ **Artist Not Found**\n"
        "The artist could not be found on Spotify.\n"
        "Please check the spelling and try again."
    )
    
    EMPTY_PLAYLIST = (
        "❌ **Empty Playlist**\n"
        "The playlist you selected doesn't contain any tracks.\n"
        "Please choose a playlist with at least one song."
    )
    
    EMPTY_ALBUM = (
        "❌ **Empty Album**\n"
        "The album you selected doesn't contain any tracks.\n"
        "Please choose a different album."
    )
    
    SPOTIFY_API_ERROR = (
        "❌ **Spotify API Error**\n"
        "There was an error communicating with Spotify.\n"
        "Please try again in a moment."
    )
    
    OAUTH_REQUIRED = (
        "🔐 **Spotify Connection Required**\n"
        "You need to connect your Spotify account first.\n"
        "Use `/connect` to link your account."
    )

def validate_spotify_response(response: Optional[Dict[str, Any]], 
                             resource_type: str) -> tuple[bool, Optional[str]]:
    """
    Validate Spotify API response
    
    Args:
        response: The API response dictionary
        resource_type: Type of resource ('playlist', 'album', 'artist', 'track')
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if response is None:
        return False, ErrorMessages.SPOTIFY_API_ERROR
    
    # Check for error in response
    if 'error' in response:
        error_status = response['error'].get('status', 0)
        
        if error_status == 404:
            if resource_type == 'playlist':
                return False, ErrorMessages.PLAYLIST_NOT_FOUND
            elif resource_type == 'album':
                return False, ErrorMessages.ALBUM_NOT_FOUND
            elif resource_type == 'artist':
                return False, ErrorMessages.ARTIST_NOT_FOUND
        
        # Log the actual error for debugging
        spotify_logger.error(f"Spotify API error for {resource_type}: {response['error']}")
        return False, ErrorMessages.SPOTIFY_API_ERROR
    
    # Check for empty results
    if resource_type == 'playlist':
        tracks = response.get('tracks', {}).get('items', [])
        if not tracks:
            return False, ErrorMessages.EMPTY_PLAYLIST
    
    elif resource_type == 'album':
        tracks = response.get('tracks', {}).get('items', [])
        if not tracks:
            return False, ErrorMessages.EMPTY_ALBUM
    
    elif resource_type == 'artist':
        # For search results
        if 'artists' in response:
            artists = response['artists'].get('items', [])
            if not artists:
                return False, ErrorMessages.ARTIST_NOT_FOUND
    
    return True, None

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user.name} (ID: {bot.user.id})")
    logger.info(f"Connected to {len(bot.guilds)} guild(s)")
    
    try:
        synced = await bot.tree.sync()
        logger.info(f"Successfully synced {len(synced)} command(s)")
        for cmd in synced:
            logger.debug(f"  - /{cmd.name}: {cmd.description}")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}", exc_info=True)


@bot.event
async def on_command_error(ctx, error):
    logger.error(f"Command error in {ctx.command}: {error}", exc_info=True)


@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"Error in event {event}", exc_info=True)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    logger.error(
        f"Slash command error - User: {interaction.user.id} | "
        f"Command: {interaction.command.name if interaction.command else 'Unknown'} | "
        f"Error: {error}",
        exc_info=True
    )
    
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "An error occurred while processing your command. Please try again later.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "An error occurred. Please try again later.",
                ephemeral=True
            )
    except Exception as e:
        logger.error(f"Failed to send error message to user: {e}")

@bot.tree.command(
    name="guess",
    description="Guess the song from the lyrics. Requires spotify oauth connection.",
)
async def guess(interaction: discord.Interaction):
    logger.info(
        f"Command /guess invoked - User: {interaction.user.name} ({interaction.user.id}) | "
        f"Guild: {interaction.guild.name if interaction.guild else 'DM'}"
    )
    
    try:
        await interaction.response.send_message("To be implemented...")
        logger.debug(f"/guess command responded successfully for user {interaction.user.id}")
    except Exception as e:
        logger.error(f"Error responding to /guess command: {e}", exc_info=True)
        raise


# Example command showing error handling implementation
@bot.tree.command(
    name="play_playlist",
    description="[Example] Play a game from a Spotify playlist"
)
async def play_playlist(
    interaction: discord.Interaction,
    playlist: str
):
    """
    Example command showing how to handle playlist validation
    
    Args:
        playlist: Playlist URL or ID
    """
    logger.info(
        f"Command /play_playlist invoked - User: {interaction.user.name} ({interaction.user.id}) | "
        f"Input: {playlist}"
    )
    
    await interaction.response.defer(thinking=True)
    
    try:
        # Validate and extract playlist ID
        playlist_id = SpotifyInputValidator.extract_playlist_id(playlist)
        
        if not playlist_id:
            logger.warning(f"Invalid playlist format from user {interaction.user.id}: {playlist}")
            await interaction.followup.send(ErrorMessages.INVALID_PLAYLIST, ephemeral=True)
            return
        
        logger.info(f"Extracted playlist ID: {playlist_id}")
        
        # TODO: Replace with actual Spotify API call
        # For now, simulate API response
        # spotify_response = await fetch_spotify_playlist(playlist_id)
        spotify_response = None  # Simulated response
        
        # Validate the response
        is_valid, error_message = validate_spotify_response(spotify_response, 'playlist')
        
        if not is_valid:
            logger.warning(f"Invalid Spotify response for playlist {playlist_id}")
            await interaction.followup.send(error_message, ephemeral=True)
            return
        
        # If we get here, the playlist is valid
        await interaction.followup.send(
            f" Successfully loaded playlist! (ID: {playlist_id})\n"
            "This is a placeholder - integrate with your Spotify API implementation."
        )
        
    except Exception as e:
        logger.error(f"Error in /play_playlist command: {e}", exc_info=True)
        await interaction.followup.send(
            ErrorMessages.SPOTIFY_API_ERROR,
            ephemeral=True
        )

# Helper function for logging Spotify API calls
def log_spotify_request(method, url, params=None, status_code=None, response_time=None):
    """Log Spotify API requests with details"""
    log_msg = f"Spotify API {method} {url}"
    if params:
        log_msg += f" | Params: {params}"
    if status_code:
        log_msg += f" | Status: {status_code}"
    if response_time:
        log_msg += f" | Response time: {response_time:.2f}s"
    
    if status_code and status_code >= 400:
        spotify_logger.error(log_msg)
    else:
        spotify_logger.info(log_msg)


# Helper function for logging OAuth events
def log_oauth_event(event_type, user_id, success=True, details=None):
    """Log OAuth-related events"""
    log_msg = f"OAuth {event_type} - User: {user_id} | Success: {success}"
    if details:
        log_msg += f" | Details: {details}"
    
    if success:
        oauth_logger.info(log_msg)
    else:
        oauth_logger.warning(log_msg)
        
if __name__ == "__main__":
    try:
        logger.info("Starting bot...")
        bot.run(TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        raise
