import os
import re
import socket
import struct
import asyncio
import discord
from discord import app_commands

# =========================
# BOT SETTINGS
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")
SERVER_IP = "meowgg.playwithbao.com"

# Keep these private in your host/environment variables.
RCON_HOST = os.getenv("RCON_HOST", SERVER_IP)
RCON_PORT = int(os.getenv("RCON_PORT", "25575"))
RCON_PASSWORD = os.getenv("RCON_PASSWORD")


# =========================
# RCON
# =========================

def _recv_exact(sock, size):
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("RCON connection closed unexpectedly.")
        data += chunk
    return data


def _recv_packet(sock):
    length = struct.unpack("<i", _recv_exact(sock, 4))[0]
    packet = _recv_exact(sock, length)

    request_id, packet_type = struct.unpack("<ii", packet[:8])
    payload = packet[8:-2].decode("utf-8", errors="replace")
    return request_id, packet_type, payload


def _send_packet(sock, request_id, packet_type, payload):
    body = (
        struct.pack("<ii", request_id, packet_type)
        + payload.encode("utf-8")
        + b"\x00\x00"
    )
    sock.sendall(struct.pack("<i", len(body)) + body)


def rcon_command(command):
    """Send one command to the Minecraft server through RCON."""
    if not RCON_PASSWORD:
        raise RuntimeError("RCON_PASSWORD is not set.")

    with socket.create_connection((RCON_HOST, RCON_PORT), timeout=8) as sock:
        # Authenticate
        _send_packet(sock, 1, 3, RCON_PASSWORD)
        auth_id, _, _ = _recv_packet(sock)

        if auth_id == -1:
            raise PermissionError("RCON authentication failed.")

        # Run command
        _send_packet(sock, 2, 2, command)
        response_id, _, response = _recv_packet(sock)

        if response_id == -1:
            raise RuntimeError("RCON command failed.")

        return response.strip()


def clean_minecraft_text(text):
    # Remove Minecraft legacy color codes such as §a and &a.
    text = re.sub(r"§[0-9A-FK-ORa-fk-or]", "", text)
    text = re.sub(r"&[0-9A-FK-ORa-fk-or]", "", text)
    return text.strip()


async def papi_parse(player, placeholder):
    command = f"papi parse {player} {placeholder}"
    result = await asyncio.to_thread(rcon_command, command)
    return clean_minecraft_text(result)


def format_playtime(value):
    """
    Statistic time_played is commonly returned as ticks.
    If the placeholder already returns formatted text, keep it as-is.
    """
    cleaned = value.replace(",", "").strip()

    if not cleaned.isdigit():
        return value

    ticks = int(cleaned)
    total_seconds = ticks // 20

    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")

    return " ".join(parts)


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

@tree.command(name="profile", description="View a live Meow.gg player profile")
@app_commands.describe(player="Minecraft player name")
async def profile(interaction: discord.Interaction, player: str):
    await interaction.response.defer()

    try:
        rank, kills, deaths, playtime = await asyncio.gather(
            papi_parse(player, "%luckperms_primary_group_name%"),
            papi_parse(player, "%statistic_player_kills%"),
            papi_parse(player, "%statistic_deaths%"),
            papi_parse(player, "%statistic_time_played%"),
        )

        # PlaceholderAPI usually leaves an unknown placeholder unchanged.
        failed_values = [rank, kills, deaths, playtime]
        if any(value.startswith("%") and value.endswith("%") for value in failed_values):
            await interaction.followup.send(
                f"❌ I couldn't get all profile data for **{player}**.\n"
                "Check that the player exists and the PlaceholderAPI expansions are loaded.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="🐱 MEOW.GG PLAYER PROFILE",
            description=f"### {player}",
            color=discord.Color.blurple(),
        )

        embed.add_field(name="👤 Name", value=player, inline=True)
        embed.add_field(name="👑 Rank", value=rank or "Unknown", inline=True)
        embed.add_field(name="⚔️ Kills", value=kills or "0", inline=True)
        embed.add_field(name="💀 Deaths", value=deaths or "0", inline=True)
        embed.add_field(
            name="⏱️ Playtime",
            value=format_playtime(playtime) if playtime else "0m",
            inline=True,
        )

        embed.set_footer(text="Meow.gg • Live Player Profile")
        await interaction.followup.send(embed=embed)

    except PermissionError:
        await interaction.followup.send(
            "❌ RCON login failed. Check `RCON_PASSWORD`.",
            ephemeral=True,
        )
    except (ConnectionError, TimeoutError, OSError):
        await interaction.followup.send(
            "❌ I couldn't connect to the Minecraft server through RCON. "
            "Check `RCON_HOST`, `RCON_PORT`, and whether the RCON port is open.",
            ephemeral=True,
        )
    except Exception as error:
        print(f"/profile error: {error}")
        await interaction.followup.send(
            "❌ Something went wrong while getting the Minecraft profile.",
            ephemeral=True,
        )


# =========================
# TEXT COMMANDS
# =========================

@client.event
async def on_message(message):
    if message.author.bot:
        return

    msg = message.content.lower().strip()

    if msg == "ip" or msg == "!ip":
        await message.channel.send(
            f"🐱 **MEOW.GG SERVER IP**\n"
            f"🌐 `{SERVER_IP}`\n"
            f"✨ Join the server!"
        )


# =========================
# START BOT
# =========================

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set.")

client.run(TOKEN)
