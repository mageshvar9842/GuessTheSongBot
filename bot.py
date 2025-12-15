import json
import discord
from discord.ext import commands

with open("config.json") as f:
    config = json.load(f)

TOKEN = config["DISCORD_TOKEN"]
BOT_ID = config["DISCORD_BOT_ID"]

bot = commands.Bot(
    command_prefix=None,
    help_command=None,
    is_case_insensitive=True,
    intents=discord.Intents.all(),
)

attempts = {}

ANSWER = "test song"

@bot.event
async def on_ready():
    print("Ready!")
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} commands")

@bot.tree.command(
    name="guess",
    description="Guess the song from the lyrics. Requires spotify oauth connection.",
)
async def guess(interaction: discord.Interaction, song: str):
    user_id = interaction.user.id

    if user_id not in attempts:
        attempts[user_id] = 0

    if song.lower() == ANSWER.lower():
        attempts.pop(user_id, None)
        embed = discord.Embed(
            title="Correct!",
            description="You guessed the song.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
        return

    attempts[user_id] += 1

    if attempts[user_id] >= 3:
        attempts.pop(user_id, None)
        embed = discord.Embed(
            title="Game Over",
            description="You used all attempts.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    embed = discord.Embed(
        title="Wrong Guess",
        description=f"Attempts left: {3 - attempts[user_id]}",
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
