import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
import yt_dlp as youtube_dl
import asyncio

# ---------- FLASK (keep alive) ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot está online!"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

Thread(target=run_web).start()
# ---------------------------------------

# ---------- DISCORD BOT ----------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Fila de músicas por guild
queue = {}

ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True
}

# ===== EVENTO ON_READY =====
@bot.event
async def on_ready():
    print(f"🤖 Bot conectado como {bot.user}")

# ===== COMANDO !PING =====
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# ===== FUNÇÃO PARA TOCAR PRÓXIMA MÚSICA =====
async def play_next(ctx):
    if not queue.get(ctx.guild.id):
        await ctx.send("Fila vazia! 😴")
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        return

    song = queue[ctx.guild.id].pop(0)
    url = song['url']
    title = song['title']
    thumbnail = song['thumbnail']
    duration = song['duration']

    voice_channel = ctx.author.voice.channel
    if not ctx.voice_client:
        vc = await voice_channel.connect()
    else:
        vc = ctx.voice_client

    vc.play(discord.FFmpegPCMAudio(url), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))

    embed = discord.Embed(title="🎶 Tocando agora:", description=f"**{title}**", color=0x00ff00)
    embed.add_field(name="Duração", value=duration, inline=True)
    embed.set_thumbnail(url=thumbnail)
    await ctx.send(embed=embed)

# ===== COMANDO !PLAY =====
@bot.command()
async def play(ctx, url):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("Você precisa estar em um canal de voz!")
        return

    if ctx.guild.id not in queue:
        queue[ctx.guild.id] = []

    # Extrair info do YouTube
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']
        title = info.get('title', 'Desconhecido')
        thumbnail = info.get('thumbnail', '')
        duration_sec = info.get('duration', 0)
        minutes = duration_sec // 60
        seconds = duration_sec % 60
        duration = f"{minutes}:{seconds:02}"

    queue[ctx.guild.id].append({
        'url': audio_url,
        'title': title,
        'thumbnail': thumbnail,
        'duration': duration
    })

    await ctx.send(f"✅ Adicionado à fila: **{title}**")

    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await play_next(ctx)

# ===== COMANDO !SKIP =====
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Música pulada!")
    else:
        await ctx.send("Não há música tocando agora!")

# ===== COMANDO !STOP =====
@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        queue[ctx.guild.id] = []
        await ctx.send("⏹️ Música parada e fila limpa!")
    else:
        await ctx.send("O bot não está em nenhum canal de voz!")

# ===== COMANDO !QUEUE =====
@bot.command()
async def queue_list(ctx):
    if ctx.guild.id not in queue or len(queue[ctx.guild.id]) == 0:
        await ctx.send("A fila está vazia! 😴")
        return

    embed = discord.Embed(title="📜 Fila de músicas", color=0x00ff00)
    for i, song in enumerate(queue[ctx.guild.id], start=1):
        embed.add_field(name=f"{i}. {song['title']}", value=f"Duração: {song['duration']}", inline=False)
    await ctx.send(embed=embed)

# ===== INICIAR BOT =====
bot.run(TOKEN)
