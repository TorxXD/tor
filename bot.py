import discord
from discord.ext import commands
import os
import requests # Librería para hacer peticiones HTTP
import asyncio
import aiohttp # Se utiliza para hacer peticiones HTTP asíncronas

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

async def check_bedrock_status_http(ip: str, port: int, timeout: int = 10):
    """
    Consulta el estado de un servidor de Minecraft Bedrock usando un servicio de consulta HTTP.
    Devuelve un diccionario con los datos o None si falla.
    """
    # URL de un servicio público de consulta de Bedrock (Ejemplo: mcstatus.io o similar)
    # NOTA: La URL https://pmt.mcpe.fun/ping/ requiere que se le envíen los datos de IP y puerto, 
    # por lo que usaremos un servicio estándar de MCBE Query para simplificar la implementación.
    api_url = f"https://api.mcstatus.io/v2/status/bedrock/{ip}:{port}"
    
    try:
        # Usamos aiohttp para peticiones asíncronas, necesario en discord.py
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=timeout) as response:
                
                # Si la respuesta HTTP no es 200 (OK), el servidor de consulta falló.
                if response.status != 200:
                    print(f"Error de API: {response.status}")
                    return None
                
                data = await response.json()
                return data
                
    except asyncio.TimeoutError:
        print("Timeout al consultar el servicio.")
        return {"online": False, "error": "Timeout de consulta"}
    except Exception as e:
        print(f"Error desconocido en la consulta HTTP: {e}")
        return None

# --- CONFIGURACIÓN DEL BOT ---

# 1. Habilitar intents
intents = discord.Intents.default()
intents.message_content = True 

# 2. DEFINICIÓN DEL OBJETO BOT 
bot = commands.Bot(command_prefix=".", intents=intents)

# --- COMANDOS DEL BOT ---

@bot.command()
async def ping(ctx, *, arg):
    """
    Comando para consultar el estado de un servidor de Minecraft Bedrock (usando HTTP).
    Uso: .ping ip:port (Puerto por defecto: 19132)
    """
    arg = arg.replace(":", " ")
    args = arg.split()
    
    if len(args) != 2:
        await ctx.send("`.ping ip:port` o `.ping ip port')")
        return

    ip, port_str = args
    try:
        port = int(port_str)
    except ValueError:
        await ctx.send("El puerto debe ser un número válido")
        return

    # Consultar el estado del servidor a través de la API
    data = await check_bedrock_status_http(ip, port)
    
    embed = discord.Embed(title="Estado del Servidor", color=0x3498db)
    
    # Manejar errores de consulta
    if data is None:
        embed.description = "No se pudo conectar con el servicio"
    elif data.get('online') is False:
        # El servicio reporta que el servidor de MCBE está offline.
        embed.description = f"Servidor `{ip}:{port}`: **Server Down** 🔴"
        
    elif data.get('online') is True:
        # Servidor online, mostrar detalles
        latency = data.get('round_trip_latency', 'N/A')
        players_online = data['players']['online']
        players_max = data['players']['max']
        motd = data['motd']['clean']
        version = data['version']['name']
        
        # Clasificación del Ping
        if isinstance(latency, (int, float)):
            ms = int(latency)
            ping_status = f"**{ms} ms**"
            if ms > 600:
                ping_status += "\nAlto ping"
            elif ms > 200:
                ping_status += "\nPing lento"
            else:
                ping_status += "\nPing normal"
        else:
            ping_status = "N/A"
            
        embed.description = f"✅ Servidor `{ip}:{port}`: **Online**"
        
        embed.add_field(name="🌐 Latencia (Ping)", value=ping_status, inline=True)
        embed.add_field(name="👥 Jugadores", value=f"{players_online}/{players_max}", inline=True)
        embed.add_field(name="💬 MOTD", value=f"```\n{motd}\n```", inline=False)
        embed.add_field(name="⚙️ Versión", value=version, inline=True)
        
    embed.set_footer(text="Consulta vía API HTTP")
    await ctx.send(embed=embed)

# --- EJECUCIÓN DEL SCRIPT ---

if __name__ == "__main__":
    token = get_token() 
    bot.run(token)

