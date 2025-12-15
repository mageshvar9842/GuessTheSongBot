import json
import random

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

active_games = {}


def get_embed_color(guesses_left, max_guesses):
    if guesses_left > max_guesses * 0.6:
        return discord.Color.green()
    elif guesses_left > max_guesses * 0.3:
        return discord.Color.yellow()
    else:
        return discord.Color.red()


def create_game_embed(song_hint, guesses_left, max_guesses, previous_guesses=None):
    color = get_embed_color(guesses_left, max_guesses)
    
    embed = discord.Embed(
        title="🎵 Guess the Song!",
        description=f"**Hint:** {song_hint}",
        color=color
    )
    
    embed.add_field(
        name="Guesses Remaining",
        value=f"{guesses_left}/{max_guesses}",
        inline=True
    )
    
    if previous_guesses:
        guesses_text = "\n".join([f"❌ {guess}" for guess in previous_guesses[-5:]])
        embed.add_field(
            name="Recent Guesses",
            value=guesses_text if guesses_text else "None yet",
            inline=False
        )
    
    return embed


def create_result_embed(won, correct_song, artist, guesses_made, max_guesses):
    if won:
        color = discord.Color.gold()
        title = "🎉 Correct!"
        description = f"You guessed it right!\n**{correct_song}** by **{artist}**"
    else:
        color = discord.Color.dark_red()
        title = "💔 Game Over"
        description = f"The correct answer was:\n**{correct_song}** by **{artist}**"
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    
    embed.add_field(
        name="Guesses Used",
        value=f"{guesses_made}/{max_guesses}",
        inline=True
    )
    
    return embed


@bot.event
async def on_ready():
    print("Ready!")
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} commands")


@bot.tree.command(
    name="guess",
    description="Guess the song from the lyrics. Requires spotify oauth connection.",
)
async def guess(interaction: discord.Interaction):
    user_id = interaction.user.id
    
    if user_id in active_games:
        await interaction.response.send_message(
            "You already have an active game! Finish it first.",
            ephemeral=True
        )
        return
    
    songs = [
        {"title": "Bohemian Rhapsody", "artist": "Queen", "hint": "Is this the real life? Is this just fantasy?"},
        {"title": "Imagine", "artist": "John Lennon", "hint": "Imagine there's no heaven"},
        {"title": "Smells Like Teen Spirit", "artist": "Nirvana", "hint": "Load up on guns, bring your friends"},
        {"title": "Billie Jean", "artist": "Michael Jackson", "hint": "She was more like a beauty queen"},
        {"title": "Hotel California", "artist": "Eagles", "hint": "On a dark desert highway"}
    ]
    
    selected_song = random.choice(songs)
    max_guesses = 6
    
    active_games[user_id] = {
        "song": selected_song["title"],
        "artist": selected_song["artist"],
        "guesses_left": max_guesses,
        "max_guesses": max_guesses,
        "previous_guesses": []
    }
    
    embed = create_game_embed(
        selected_song["hint"],
        max_guesses,
        max_guesses
    )
    
    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="answer",
    description="Submit your guess for the current song game."
)
async def answer(interaction: discord.Interaction, guess: str):
    user_id = interaction.user.id
    
    if user_id not in active_games:
        await interaction.response.send_message(
            "You don't have an active game! Use /guess to start one.",
            ephemeral=True
        )
        return
    
    game = active_games[user_id]
    correct_song = game["song"].lower().strip()
    user_guess = guess.lower().strip()
    
    if user_guess == correct_song:
        guesses_made = game["max_guesses"] - game["guesses_left"] + 1
        embed = create_result_embed(
            True,
            game["song"],
            game["artist"],
            guesses_made,
            game["max_guesses"]
        )
        del active_games[user_id]
        await interaction.response.send_message(embed=embed)
        return
    
    game["guesses_left"] -= 1
    game["previous_guesses"].append(guess)
    
    if game["guesses_left"] <= 0:
        embed = create_result_embed(
            False,
            game["song"],
            game["artist"],
            game["max_guesses"],
            game["max_guesses"]
        )
        del active_games[user_id]
        await interaction.response.send_message(embed=embed)
        return
    
    embed = create_game_embed(
        "Try again! Think about the hint...",
        game["guesses_left"],
        game["max_guesses"],
        game["previous_guesses"]
    )
    
    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="endgame",
    description="End your current song guessing game."
)
async def endgame(interaction: discord.Interaction):
    user_id = interaction.user.id
    
    if user_id not in active_games:
        await interaction.response.send_message(
            "You don't have an active game!",
            ephemeral=True
        )
        return
    
    game = active_games[user_id]
    embed = discord.Embed(
        title="Game Ended",
        description=f"The answer was:\n**{game['song']}** by **{game['artist']}**",
        color=discord.Color.blue()
    )
    
    del active_games[user_id]
    await interaction.response.send_message(embed=embed)


bot.run(TOKEN)
