import discord
from discord.ext import commands
import socket
import time
import os

# ... (El resto del código de setup de token e intents permanece igual) ...

def ping_server(ip, port, timeout=3):
    """
    Intenta establecer una conexión TCP con el servidor para medir la latencia.
    NOTA: Minecraft Bedrock usa UDP (RakNet). Esto solo mide la latencia de conexión TCP.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout) # Aumentar el timeout por si el servidor tarda en responder
    start_time = time.time()
    
    try:
        # 1. Intenta la conexión
        s.connect((ip, int(port)))
        
        # 2. Envía un byte de datos para forzar la respuesta de latencia
        # Aunque es TCP, ayuda a obtener una mejor medida que solo 'connect'
        s.sendall(b'\x01') 
        
        # 3. Espera a recibir una respuesta mínima (puede ser vacío, solo nos interesa el tiempo)
        s.recv(1) 
        
        end_time = time.time()
        s.close()
        
        # Calcula el tiempo en milisegundos
        ms = int((end_time - start_time) * 1000)
        return ms
        
    except ConnectionRefusedError:
        # El servidor rechazó explícitamente la conexión
        return -1 # Usaremos -1 para indicar rechazo (Server Offline)
    except socket.timeout:
        # La conexión excedió el tiempo de espera
        return 0 # Usaremos 0 para indicar timeout (Server Lag/Slow)
    except Exception:
        # Cualquier otro error (ej. IP/puerto inválido, etc.)
        return None

@bot.command()
async def ping(ctx, *, arg):
    arg = arg.replace(":", " ")
    args = arg.split()
    if len(args) != 2:
        await ctx.send("Formato incorrecto. Usa `.ping ip:port` o `.ping ip port`")
        return

    ip, port = args
    ms = ping_server(ip, port)
    embed = discord.Embed(title="Ping Result", color=0x3498db)
    
    # Manejo de los nuevos códigos de error
    if ms is None:
        embed.description = f"Servidor `{ip}:{port}`: **Error Desconocido**"
    elif ms == -1:
        embed.description = f"Servidor `{ip}:{port}`: **Servidor Rechazó Conexión** (Offline o puerto equivocado)"
    elif ms == 0:
        embed.description = f"Servidor `{ip}:{port}`: **Timeout** (Ping excesivamente alto o bloqueado)"
    elif ms > 600:
        embed.description = f"Servidor `{ip}:{port}`: **{ms} ms**\nServer con muy alto ping"
    elif ms > 200:
        embed.description = f"Servidor `{ip}:{port}`: **{ms} ms**\nServer lento"
    else:
        embed.description = f"Servidor `{ip}:{port}`: **{ms} ms**\nPing Normal"
        
    embed.set_footer(text="Ping")
    await ctx.send(embed=embed)
