import discord
from discord.ext import commands
# Otras librerías necesarias
import os
import time
import socket

# Librería externa requerida para Bedrock
from mcstatus.server import BedrockServer

TOKEN_FILE = "token.txt"

# ... (Resto de tu código de setup de token e intents) ...
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix=".", intents=intents)


async def ping_bedrock_server(ip, port, timeout=5):
    """
    Realiza un ping nativo a un servidor de Minecraft Bedrock (UDP).
    Devuelve la latencia en ms o None si falla.
    """
    try:
        # Crea la instancia del servidor Bedrock
        server = BedrockServer(ip, int(port))
        
        # Llama a async_status (debe ser awaitable)
        status = await server.async_status(timeout=timeout)
        
        # El ping (latencia) ya está en el objeto de estado
        ms = int(status.latency)
        return ms
        
    except Exception as e:
        # Cualquier error (timeout, servidor inaccesible, etc.) devuelve None
        print(f"Error al hacer ping a {ip}:{port}: {e}")
        return None

# Y ahora actualizamos tu comando para que sea 'await'
@bot.command()
async def ping(ctx, *, arg):
    arg = arg.replace(":", " ")
    args = arg.split()
    if len(args) != 2:
        # Usa el puerto por defecto de Bedrock si no se especifica
        await ctx.send("`.ping ip:port` o `.ping ip port`")
        return

    ip, port_str = args
    port = int(port_str)
    
    # --- CAMBIO CLAVE: Usar la función asíncrona ---
    ms = await ping_bedrock_server(ip, port)
    # ------------------------------------------------
    
    embed = discord.Embed(title="Ping Result (Minecraft Bedrock)", color=0x3498db)
    
    if ms is None:
        embed.description = f"Servidor `{ip}:{port}`: **Server Down** o inaccesible (UDP/RakNet)"
    elif ms > 600:
        embed.description = f"Servidor `{ip}:{port}`: **{ms} ms**\nServer con muy alto ping"
    elif ms > 200:
        embed.description = f"Servidor `{ip}:{port}`: **{ms} ms**\nServer lento"
    else:
        embed.description = f"Servidor `{ip}:{port}`: **{ms} ms**\nPing Normal"
        
    embed.set_footer(text="Ping Bedrock (UDP)")
    await ctx.send(embed=embed)

if __name__ == "__main__":
    token = get_token()
    bot.run(token)
