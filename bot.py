import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# ---------- FLASK (keep alive) ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot está online!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_web).start()
# ---------------------------------------

# ---------- DISCORD BOT ----------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Bot conectado como {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

bot.run(TOKEN)
# --------------------------------
