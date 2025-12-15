import json
import logging
from datetime import datetime

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


# Helper function for logging Spotify API calls (to be used in future implementation)
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


# Helper function for logging OAuth events (to be used in future implementation)
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
