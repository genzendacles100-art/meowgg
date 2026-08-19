import os
import json
import discord
from discord import app_commands

# =========================
# BOT SETTINGS
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")
SERVER_IP = "meowgg.playwithbao.com"
PROFILE_FILE = "profiles.json"


# =========================
# PROFILE DATA
# =========================

def load_profiles():
    if not os.path.exists(PROFILE_FILE):
        return {}

    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def save_profiles(profiles):
    with open(PROFILE_FILE, "w", encoding="utf-8") as file:
        json.dump(profiles, file, indent=4)


# =========================
# BOT SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


# =========================
# BOT ONLINE
# =========================

@client.event
async def on_ready():
    await tree.sync()
    print(f"Meow.gg bot is ONLINE as {client.user}")
    print("Slash commands synced.")


# =========================
# /PROFILE COMMAND
# =========================

@tree.command(name="profile", description="View a Meow.gg player profile")
@app_commands.describe(player="Minecraft player name")
async def profile(interaction: discord.Interaction, player: str):
    profiles = load_profiles()
    key = player.lower()

    if key not in profiles:
        await interaction.response.send_message(
            f"❌ No profile data was found for **{player}** yet.",
            ephemeral=True,
        )
        return

    data = profiles[key]

    embed = discord.Embed(
        title="🐱 MEOW.GG PLAYER PROFILE",
        description=f"### {data.get('name', player)}",
        color=discord.Color.blurple(),
    )

    embed.add_field(name="👑 Rank", value=data.get("rank", "Unknown"), inline=True)
    embed.add_field(name="⚔️ Kills", value=str(data.get("kills", 0)), inline=True)
    embed.add_field(name="💀 Deaths", value=str(data.get("deaths", 0)), inline=True)
    embed.add_field(name="⏱️ Playtime", value=data.get("playtime", "0h"), inline=True)

    embed.set_footer(text="Meow.gg • Player Profile")

    await interaction.response.send_message(embed=embed)


# =========================
# /SETPROFILE COMMAND
# Admin-only temporary profile updater.
# This can later be replaced by automatic Minecraft syncing.
# =========================

@tree.command(name="setprofile", description="Set a Meow.gg player profile")
@app_commands.describe(
    player="Minecraft player name",
    rank="Player rank",
    kills="Player kills",
    deaths="Player deaths",
    playtime="Example: 2d 6h",
)
@app_commands.checks.has_permissions(administrator=True)
async def setprofile(
    interaction: discord.Interaction,
    player: str,
    rank: str,
    kills: int,
    deaths: int,
    playtime: str,
):
    profiles = load_profiles()

    profiles[player.lower()] = {
        "name": player,
        "rank": rank,
        "kills": kills,
        "deaths": deaths,
        "playtime": playtime,
    }

    save_profiles(profiles)

    await interaction.response.send_message(
        f"✅ Updated **{player}**'s Meow.gg profile.",
        ephemeral=True,
    )


@setprofile.error
async def setprofile_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ You need Administrator permission to use this command.",
            ephemeral=True,
        )
        return

    raise error


# =========================
# TEXT COMMANDS
# =========================

@client.event
async def on_message(message):

    # Don't respond to other bots
    if message.author.bot:
        return

    msg = message.content.lower().strip()

    # IP COMMAND
    if msg == "ip" or msg == "!ip":
        await message.channel.send(
            f"🐱 **MEOW.GG SERVER IP**\n"
            f"🌐 `{SERVER_IP}`\n"
            f"✨ Join the server!"
        )


# =========================
# START BOT
# =========================

client.run(TOKEN)
