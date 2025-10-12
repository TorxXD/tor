import discord
from discord.ext import commands
import socket
import time
import os

TOKEN_FILE = "token.txt"

def get_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    else:
        token = input("Introduce el token de tu bot de Discord: ").strip()
        with open(TOKEN_FILE, "w") as f:
            f.write(token)
        return token

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=".", intents=intents)

def ping_server(ip, port, timeout=2):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    start_time = time.time()
    try:
        s.connect((ip, int(port)))
        end_time = time.time()
        ms = int((end_time - start_time) * 1000)
        s.close()
        return ms
    except Exception:
        return None

@bot.command()
async def ping(ctx, *, arg):
    arg = arg.replace(":", " ")
    args = arg.split()
    if len(args) != 2:
        await ctx.send("`.ping ip:port` o `.ping ip port`")
        return

    ip, port = args
    ms = ping_server(ip, port)
    embed = discord.Embed(title="Ping Result", color=0x3498db)
    if ms is None:
        embed.description = f"Servidor `{ip}:{port}`: **Server Down**"
    elif ms > 600:
        embed.description = f"Servidor `{ip}:{port}`: **{ms} ms**\n⚠️ Server con muy alto ping"
    elif ms > 200:
        embed.description = f"Servidor `{ip}:{port}`: **{ms} ms**\n⚠️ Server lento"
    else:
        embed.description = f"Servidor `{ip}:{port}`: **{ms} ms**"
    embed.set_footer(text="Ping")
    await ctx.send(embed=embed)

if __name__ == "__main__":
    token = get_token()
    bot.run(token)
