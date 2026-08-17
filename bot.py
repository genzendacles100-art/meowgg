import os
import discord

# =========================
# BOT SETTINGS
# =========================

TOKEN = TOKEN = os.getenv("DISCORD_TOKEN")
SERVER_IP = "meowgg.playwithbao.com"


# =========================
# BOT SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


# =========================
# BOT ONLINE
# =========================

@client.event
async def on_ready():
    print(f"Meow.gg bot is ONLINE as {client.user}")


# =========================
# COMMANDS
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