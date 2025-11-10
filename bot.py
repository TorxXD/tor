import discord
from discord.ext import commands
import os
import asyncio
import aiohttp

# --- CONFIGURACIÓN Y FUNCIONES AUXILIARES ---
TOKEN_FILE = "token.txt"
ENV_TOKEN_NAME = "DISCORD_TOKEN"

def get_token():
    """Obtiene el token del entorno (DISCORD_TOKEN) o del archivo token.txt para desarrollo local.
    En entornos no interactivos (como GitHub Actions) el token debe venir por la variable de entorno.
    """
    # 1) Preferir variable de entorno (usada por GitHub Actions: repo secret -> DISCORD_TOKEN)
    token = os.getenv(ENV_TOKEN_NAME)
    if token:
        return token.strip()

    # 2) Fallback a token.txt para desarrollo en local
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()

    # 3) Si no hay token, lanzar error claro (evitar input() en entornos no interactivos)
    raise RuntimeError(
        f"No se encontró token. Configure la variable de entorno {ENV_TOKEN_NAME} (recomendado) "
        "o cree un archivo token.txt con el token para desarrollo local."
    )

async def check_bedrock_status_http(ip: str, port: int, timeout: int = 10):
    """
    Consulta el estado de un servidor de Minecraft Bedrock usando un servicio de consulta HTTP.
    Devuelve un diccionario con los datos o None si falla.
    """
    api_url = f"https://api.mcstatus.io/v2/status/bedrock/{ip}:{port}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=timeout) as response:
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
        await ctx.send("`.ping ip:port` o `.ping ip port`")
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
        embed.description = f"Servidor `{ip}:{port}`: **Server Down** 🔴"
    elif data.get('online') is True:
        latency = data.get('round_trip_latency', 'N/A')
        players_online = data['players'].get('online', 'N/A')
        players_max = data['players'].get('max', 'N/A')
        motd = data.get('motd', {}).get('clean', '')
        version = data.get('version', {}).get('name', 'N/A')

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
