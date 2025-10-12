import discord
from discord.ext import commands
import os
import time
import socket # Se mantiene para la estructura, aunque no se usa para el ping de MCBE
from mcstatus.server import BedrockServer # Librería para ping Bedrock (UDP)

# --- CONFIGURACIÓN Y FUNCIONES AUXILIARES ---
TOKEN_FILE = "token.txt"

def get_token():
    """Obtiene el token del archivo o lo solicita al usuario."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    else:
        token = input("Introduce el token de tu bot de Discord: ").strip()
        with open(TOKEN_FILE, "w") as f:
            f.write(token)
        return token

async def ping_bedrock_server(ip, port, timeout=5):
    """
    Realiza un ping nativo a un servidor de Minecraft Bedrock (UDP) usando mcstatus.
    Devuelve la latencia en ms o None si falla.
    """
    try:
        # Crea la instancia del servidor Bedrock
        server = BedrockServer(ip, int(port))
        
        # Consulta el estado de forma asíncrona
        status = await server.async_status(timeout=timeout)
        
        # La latencia ya viene en el objeto status
        ms = int(status.latency)
        return ms
        
    except Exception as e:
        # Error al hacer ping (timeout, servidor inaccesible, etc.)
        print(f"Error al hacer ping a {ip}:{port}: {e}")
        return None

# --- CONFIGURACIÓN DEL BOT ---

# 1. Habilitar intents, incluyendo message_content para leer comandos
intents = discord.Intents.default()
intents.message_content = True 

# 2. DEFINICIÓN DEL OBJETO BOT (debe ir antes del decorador @bot.command())
bot = commands.Bot(command_prefix=".", intents=intents)

# --- COMANDOS DEL BOT ---

@bot.command()
async def ping(ctx, *, arg):
    """
    Comando para hacer ping a un servidor de Minecraft Bedrock.
    Uso: .ping ip:port (El puerto por defecto de Bedrock es 19132)
    """
    arg = arg.replace(":", " ")
    args = arg.split()
    
    if len(args) != 2:
        await ctx.send("`.ping ip:port` o `.ping ip port`)")
        return

    ip, port_str = args
    try:
        port = int(port_str)
    except ValueError:
        await ctx.send("El puerto debe ser un número válido.")
        return

    # Usar la función asíncrona de ping de Bedrock
    ms = await ping_bedrock_server(ip, port)
    
    embed = discord.Embed(title="Ping Result (Minecraft Bedrock)", color=0x3498db)
    
    if ms is None:
        embed.description = f"Servidor `{ip}:{port}`: **Server Down** o inaccesible (UDP/RakNet)"
    elif ms > 600:
        embed.description = f"Servidor `{ip}:{port}`: **{ms} ms**\nServer con muy alto ping"
    elif ms > 200:
        embed.description = f"Servidor `{ip}:{port}`: **{ms} ms**\nServer lento"
    else:
        embed.description = f"Servidor `{ip}:{port}`: **{ms} ms**\nPing Normal"
        
    embed.set_footer(text="Ping (UDP)")
    await ctx.send(embed=embed)

# --- EJECUCIÓN DEL SCRIPT ---

if __name__ == "__main__":
    token = get_token() # get_token() está definida antes
    bot.run(token)
