import random
import sys
import socket
import threading
import time
import json
import uuid
from datetime import datetime, timedelta
import signal

# CONSTANTES
TAMANIO_TABLERO = 10
BARCOS = {
    "Portaaviones": 4,
    "Buque": 3,
    "Crucero": 2,
    "Submarino": 2,
    "Lancha": 1
}

LETRAS_A_NUMEROS = {
    'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4,
    'F': 5, 'G': 6, 'H': 7, 'I': 8, 'J': 9
}
NUMEROS_A_LETRAS = {v: k for k, v in LETRAS_A_NUMEROS.items()}

# CONSTANTES DE RED - PUERTOS MODIFICADOS
BROADCAST_PORT = 6969  # Puerto del servidor
GAME_PORT = 7171       # Puerto del cliente
BROADCAST_MESSAGE = "HUNDIR_FLOTA_DISPONIBLE"
TIMEOUT_TURNO = 30
TIMEOUT_CONNECTION = 10
MAX_RECONNECT_ATTEMPTS = 3
TIEMPO_ENTRE_DISPAROS = 2  # Segundos entre disparos automáticos

# VARIABLES GLOBALES DE RED
session_id = str(uuid.uuid4())
is_server = False
connection = None
connected = False
broadcast_socket = None
game_socket = None
reconnect_attempts = 0
game_active = True

# VARIABLES GLOBALES DE IA
disparos_realizados = set()
blancos_pendientes = []  # Coordenadas donde hubo impacto pero no hundido
direcciones_probadas = {}  # Para cada blanco, qué direcciones hemos probado

# FUNCIONES DE TABLERO
def crear_tablero():
    """Crea un tablero vacío de 10x10"""
    return [['X' for _ in range(TAMANIO_TABLERO)] for _ in range(TAMANIO_TABLERO)]

def poder_colocar_barco(tablero, fila, columna, tamaño, orientacion):
    """Verifica si un barco cabe en la posición dada sin superponerse"""
    if orientacion == 'H':
        if columna + tamaño > TAMANIO_TABLERO:
            return False
        return all(tablero[fila][columna + i] == 'X' for i in range(tamaño))
    else:
        if fila + tamaño > TAMANIO_TABLERO:
            return False
        return all(tablero[fila + i][columna] == 'X' for i in range(tamaño))

def colocar_barcos(tablero):
    """Coloca los barcos en posiciones aleatorias en el tablero"""
    for nombre, tamaño in BARCOS.items():
        colocado = False
        while not colocado:
            fila = random.randint(0, TAMANIO_TABLERO - 1)
            columna = random.randint(0, TAMANIO_TABLERO - 1)
            orientacion = random.choice(['H', 'V'])
            
            if poder_colocar_barco(tablero, fila, columna, tamaño, orientacion):
                for i in range(tamaño):
                    if orientacion == 'H':
                        tablero[fila][columna + i] = nombre[0]
                    else:
                        tablero[fila + i][columna] = nombre[0]
                colocado = True

def quedan_barcos(tablero):
    """Verifica si aún quedan barcos en el tablero"""
    for fila in tablero:
        for celda in fila:
            if celda not in ("X", "-", "T", "H"):
                return True
    return False

def imprimir_tablero(tablero):
    """Muestra el tablero en la terminal con letras para las filas"""
    print("  " + " ".join(str(i) for i in range(TAMANIO_TABLERO)))
    for i, fila in enumerate(tablero):
        letra_fila = NUMEROS_A_LETRAS[i]
        print(letra_fila + " " + " ".join(fila))

# FUNCIONES DE BARCOS
def encontrar_todas_posiciones_barco(tablero, letra_barco, fila, columna):
    """Encuentra todas las posiciones de un barco específico"""
    posiciones = set()
    posiciones.add((fila, columna))
    
    # Buscar en todas las direcciones para encontrar el barco completo
    cola = [(fila, columna)]
    visitados = set()
    
    while cola:
        f_actual, c_actual = cola.pop(0)
        if (f_actual, c_actual) in visitados:
            continue
        visitados.add((f_actual, c_actual))
        
        # Buscar en las 4 direcciones
        for df, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nueva_f, nueva_c = f_actual + df, c_actual + dc
            
            if (0 <= nueva_f < TAMANIO_TABLERO and 
                0 <= nueva_c < TAMANIO_TABLERO and
                (nueva_f, nueva_c) not in visitados):
                
                celda = tablero[nueva_f][nueva_c]
                if celda == letra_barco or celda == "T" or celda == "H":
                    posiciones.add((nueva_f, nueva_c))
                    cola.append((nueva_f, nueva_c))
    
    return list(posiciones)

def comprobar_hundido(tablero, letra_barco, fila, columna):
    """Comprueba si todas las partes de un barco específico han sido tocadas"""
    posiciones_barco = encontrar_todas_posiciones_barco(tablero, letra_barco, fila, columna)
    
    # Verificar si todas las posiciones del barco están tocadas (T) o hundidas (H)
    for f, c in posiciones_barco:
        celda = tablero[f][c]
        if celda != "T" and celda != "H":
            return False, posiciones_barco
    
    return True, posiciones_barco

def obtener_nombre_barco(letra_barco):
    """Devuelve el nombre completo del barco a partir de su letra inicial"""
    for nombre, _ in BARCOS.items():
        if nombre[0] == letra_barco:
            return nombre
    return None

# FUNCIONES DE IA PARA JUGADOR AUTOMATICO
def generar_disparo_inteligente():
    """Genera un disparo usando estrategia inteligente"""
    global blancos_pendientes, direcciones_probadas, disparos_realizados
    
    # Si tenemos blancos pendientes (impactos sin hundir), atacar alrededor
    if blancos_pendientes:
        return atacar_blanco_pendiente()
    
    # Si no hay blancos pendientes, usar estrategia de patrón checkerboard
    return disparo_patron_tablero()

def atacar_blanco_pendiente():
    """Ataca alrededor de un impacto previo"""
    global blancos_pendientes, direcciones_probadas, disparos_realizados
    
    blanco = blancos_pendientes[0]
    fila, columna = blanco
    
    if blanco not in direcciones_probadas:
        direcciones_probadas[blanco] = []
    
    # Direcciones: arriba, abajo, izquierda, derecha
    direcciones = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for df, dc in direcciones:
        if (df, dc) not in direcciones_probadas[blanco]:
            nueva_fila = fila + df
            nueva_columna = columna + dc
            
            if (0 <= nueva_fila < TAMANIO_TABLERO and 
                0 <= nueva_columna < TAMANIO_TABLERO and
                (nueva_fila, nueva_columna) not in disparos_realizados):
                
                direcciones_probadas[blanco].append((df, dc))
                return nueva_fila + 1, nueva_columna + 1  # Convertir a coordenadas 1-10
    
    # Si no hay más direcciones, quitar este blanco de la lista
    blancos_pendientes.remove(blanco)
    del direcciones_probadas[blanco]
    
    # Recursivamente buscar otro blanco o usar patrón
    return generar_disparo_inteligente()

def disparo_patron_tablero():
    """Usa patrón de tablero de ajedrez para máxima eficiencia"""
    global disparos_realizados
    
    # Primero intenta patrón checkerboard
    for fila in range(TAMANIO_TABLERO):
        for columna in range(TAMANIO_TABLERO):
            if (fila + columna) % 2 == 0 and (fila, columna) not in disparos_realizados:
                return fila + 1, columna + 1
    
    # Si se agotó el patrón, disparar secuencialmente
    for fila in range(TAMANIO_TABLERO):
        for columna in range(TAMANIO_TABLERO):
            if (fila, columna) not in disparos_realizados:
                return fila + 1, columna + 1
    
    # Esto no debería pasar en un juego normal
    return 1, 1

def procesar_resultado_disparo(x, y, resultado):
    """Procesa el resultado de un disparo para actualizar la estrategia"""
    global blancos_pendientes, direcciones_probadas, disparos_realizados
    
    fila, columna = x - 1, y - 1  # Convertir de coordenadas 1-10 a índices 0-9
    disparos_realizados.add((fila, columna))
    
    if "impacto" in resultado:
        # Agregar a blancos pendientes si no está ya
        if (fila, columna) not in blancos_pendientes:
            blancos_pendientes.append((fila, columna))
    
    elif "hundido" in resultado:
        # Remover el blanco actual y todos los relacionados
        if (fila, columna) in blancos_pendientes:
            blancos_pendientes.remove((fila, columna))
            if (fila, columna) in direcciones_probadas:
                del direcciones_probadas[(fila, columna)]
        
        # Remover blancos pendientes cercanos que probablemente eran parte del mismo barco
        blancos_a_remover = []
        for blanco in blancos_pendientes:
            bf, bc = blanco
            # Si está en la misma fila o columna y cerca, probablemente era del mismo barco
            if (bf == fila and abs(bc - columna) <= 3) or (bc == columna and abs(bf - fila) <= 3):
                blancos_a_remover.append(blanco)
        
        for blanco in blancos_a_remover:
            if blanco in blancos_pendientes:
                blancos_pendientes.remove(blanco)
            if blanco in direcciones_probadas:
                del direcciones_probadas[blanco]

# FUNCIONES DE MANEJO DE SEÑALES
def signal_handler(signum, frame):
    """Maneja las señales de interrupción (Ctrl+C)"""
    global connection, connected
    
    print("\n\nTe has desconectado")
    if connected:
        # Enviar mensaje de desconexión manual al oponente
        try:
            send_message({
                "tipo": "desconexion", 
                "razon": "interrupcion_manual",
                "mensaje": "El enemigo se ha desconectado"
            })
            time.sleep(0.5)  # Dar tiempo para que se envíe
        except:
            pass
        close_connection()
    sys.exit(0)

# FUNCIONES DE RED
def get_local_ip():
    """Obtiene la IP local de la máquina"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"

def send_broadcast():
    """Envía mensajes de broadcast para encontrar oponentes"""
    global broadcast_socket, session_id, connected, game_active
    
    try:
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        broadcast_socket.settimeout(1)
        
        broadcast_data = {
            "message": BROADCAST_MESSAGE,
            "session_id": session_id,
            "ip": get_local_ip(),
            "port": GAME_PORT
        }
        
        while not connected and game_active:
            try:
                message = json.dumps(broadcast_data).encode()
                broadcast_socket.sendto(message, ('<broadcast>', BROADCAST_PORT))
                print("Buscando oponentes en la red...")
                time.sleep(5)
            except socket.error as e:
                if "bloqueado" in str(e) or "blocked" in str(e):
                    print(f"Error: Puerto {BROADCAST_PORT} bloqueado. Verifica tu firewall")
                    break
                else:
                    print(f"Error enviando broadcast: {e}")
                    time.sleep(5)
    except Exception as e:
        print(f"Error configurando broadcast: {e}")
    finally:
        if broadcast_socket:
            broadcast_socket.close()

def listen_for_broadcast():
    """Escucha mensajes de broadcast de otros jugadores"""
    global connected, game_active, session_id, is_server
    
    try:
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_socket.bind(('', BROADCAST_PORT))
        listen_socket.settimeout(1)
        
        print("Esperando jugadores en la red...")
        
        while not connected and game_active:
            try:
                data, addr = listen_socket.recvfrom(1024)
                message = json.loads(data.decode())
                
                if (message.get("message") == BROADCAST_MESSAGE and 
                    message.get("session_id") != session_id):
                    
                    print(f"Oponente encontrado en {addr[0]}")
                    
                    # Decidir quién será servidor usando session_id
                    if session_id > message.get("session_id"):
                        is_server = True
                        start_server()
                    else:
                        connect_to_server(message.get("ip"), message.get("port"))
                    
                    break
                    
            except socket.timeout:
                continue
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"Error escuchando broadcasts: {e}")
                
    except Exception as e:
        print(f"Error configurando listener: {e}")
    finally:
        listen_socket.close()

def start_server():
    """Inicia el servidor de juego"""
    global game_socket, connection, connected
    
    try:
        game_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        game_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        game_socket.bind(('', GAME_PORT))
        game_socket.listen(1)
        
        print("Esperando conexión del oponente...")
        connection, addr = game_socket.accept()
        connection.settimeout(TIMEOUT_CONNECTION)
        
        print(f"Oponente conectado desde {addr[0]}")
        connected = True
        
    except Exception as e:
        print(f"Error iniciando servidor: {e}")
        connected = False

def connect_to_server(server_ip, server_port):
    """Se conecta al servidor de juego"""
    global connection, connected
    
    try:
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.settimeout(TIMEOUT_CONNECTION)
        connection.connect((server_ip, server_port))
        
        print(f"Conectado al oponente en {server_ip}:{server_port}")
        connected = True
        
    except Exception as e:
        print(f"Error conectando al servidor: {e}")
        connected = False

def send_message(message):
    """Envía un mensaje al oponente"""
    global connection, connected
    
    try:
        if connection:
            data = json.dumps(message).encode()
            connection.send(data)
            return True
    except Exception as e:
        print(f"Error enviando mensaje: {e}")
        handle_disconnection()
        return False
    return False

def receive_message(timeout=TIMEOUT_TURNO):
    """Recibe un mensaje del oponente"""
    global connection, connected, game_active
    
    try:
        if connection:
            connection.settimeout(timeout)
            data = connection.recv(1024)
            if data:
                message = json.loads(data.decode())
                
                # Verificar si es un mensaje de desconexión
                if message.get("tipo") == "desconexion":
                    if message.get("razon") == "interrupcion_manual":
                        print(message.get("mensaje", "El enemigo se ha desconectado"))
                    else:
                        print("El oponente se ha desconectado")
                    handle_disconnection()
                    return None
                
                return message
            else:
                # Conexión cerrada por el otro lado
                handle_disconnection()
                return None
    except socket.timeout:
        print("Timeout: El oponente no respondió a tiempo")
        handle_disconnection()
        return None
    except Exception as e:
        print(f"Error recibiendo mensaje: {e}")
        handle_disconnection()
        return None
    return None

def handle_disconnection():
    """Maneja la desconexión del oponente"""
    global connected, game_active, connection
    
    if connected:
        print("¡La conexión se ha perdido!")
    connected = False
    game_active = False
    if connection:
        connection.close()

def close_connection():
    """Cierra la conexión intencionalmente"""
    global connected, game_active, connection, game_socket
    
    print("Cerrando conexión...")
    connected = False
    game_active = False
    if connection:
        try:
            # Enviar mensaje de desconexión intencional
            send_message({"tipo": "desconexion", "razon": "juego_terminado"})
            time.sleep(0.5)  # Dar tiempo para que se envíe
        except:
            pass
        connection.close()
    if game_socket:
        game_socket.close()

# FUNCIONES DE JUEGO EN RED
def validar_coordenada(x, y):
    """Valida que las coordenadas estén en el rango correcto (1-10)"""
    try:
        x, y = int(x), int(y)
        return 1 <= x <= 10 and 1 <= y <= 10
    except ValueError:
        return False

def coordenada_a_indices(x, y):
    """Convierte coordenadas del protocolo (1-10) a índices del tablero (0-9)"""
    return int(x) - 1, int(y) - 1

def indices_a_coordenada(fila, columna):
    """Convierte índices del tablero (0-9) a coordenadas del protocolo (1-10)"""
    return columna + 1, fila + 1

def sincronizar_tableros():
    """Sincroniza el tamaño de los tableros entre jugadores"""
    global is_server
    
    print("Sincronizando configuración del juego...")
    
    config = {
        "filas": TAMANIO_TABLERO,
        "columnas": TAMANIO_TABLERO,
        "barcos": BARCOS
    }
    
    if is_server:
        # Servidor envía primero
        if not send_message(config):
            return False
        
        # Recibe configuración del cliente
        client_config = receive_message()
        if not client_config:
            return False
        
        # Verifica compatibilidad
        if (client_config.get("filas") != TAMANIO_TABLERO or 
            client_config.get("columnas") != TAMANIO_TABLERO):
            print("Error: Configuración de tableros incompatible")
            return False
    else:
        # Cliente recibe primero
        server_config = receive_message()
        if not server_config:
            return False
        
        # Verifica compatibilidad
        if (server_config.get("filas") != TAMANIO_TABLERO or 
            server_config.get("columnas") != TAMANIO_TABLERO):
            print("Error: Configuración de tableros incompatible")
            return False
        
        # Envía su configuración
        if not send_message(config):
            return False
    
    print("Tableros sincronizados correctamente")
    return True

def procesar_ataque_red(tablero_propio, x, y):
    """Procesa un ataque recibido por red y devuelve el resultado"""
    if not validar_coordenada(x, y):
        return {"error": "coordenada_invalida"}
    
    fila, columna = coordenada_a_indices(x, y)
    
    # Verificar si ya fue atacada
    if tablero_propio[fila][columna] in ("-", "T", "H"):
        return {"resultado": "ya_disparado"}
    
    if tablero_propio[fila][columna] == "X":
        tablero_propio[fila][columna] = "-"
        return {"resultado": "agua", "victoria": False}
    
    # Impacto en barco
    letra_barco = tablero_propio[fila][columna]
    tablero_propio[fila][columna] = "T"
    
    # Verificar si el barco está hundido
    hundido, posiciones = comprobar_hundido(tablero_propio, letra_barco, fila, columna)
    
    if hundido:
        # Marcar TODAS las posiciones del barco como hundidas
        for f, c in posiciones:
            tablero_propio[f][c] = "H"
        
        nombre_barco = obtener_nombre_barco(letra_barco)
        victoria = not quedan_barcos(tablero_propio)
        
        return {
            "resultado": "hundido",
            "barco": nombre_barco,
            "posiciones": posiciones,  # Enviar las posiciones para actualizar el tablero enemigo
            "victoria": victoria
        }
    else:
        return {"resultado": "impacto", "victoria": False}

def realizar_ataque_red(x, y):
    """Envía un ataque por red y recibe la respuesta"""
    if not validar_coordenada(x, y):
        return {"error": "coordenada_invalida"}
    
    ataque = {"x": x, "y": y}
    
    if not send_message(ataque):
        return {"error": "conexion_perdida"}
    
    respuesta = receive_message()
    if not respuesta:
        return {"error": "timeout"}
    
    return respuesta

def generar_disparo_automatico():
    """Genera un disparo automatico usando la IA"""
    return generar_disparo_inteligente()

# FUNCIÓN PRINCIPAL DE JUEGO EN RED
def juego_red():
    """Función principal que maneja el juego en red"""
    global connected, game_active, is_server, session_id, disparos_realizados
    
    # Reiniciar variables globales
    disparos_realizados = set()
    
    # Configurar manejador de señales
    signal.signal(signal.SIGINT, signal_handler)
    
    # Iniciar búsqueda de oponente
    print("\n¡HUNDIR LA FLOTA - MODO AUTÓNOMO!")
    print("Buscando oponentes automáticamente...")
    
    # Ejecutar broadcast y listener en paralelo
    broadcast_thread = threading.Thread(target=send_broadcast)
    listen_thread = threading.Thread(target=listen_for_broadcast)
    
    broadcast_thread.daemon = True
    listen_thread.daemon = True
    
    broadcast_thread.start()
    listen_thread.start()
    
    # Esperar hasta que se establezca conexión
    while not connected and game_active:
        time.sleep(0.1)
    
    if not game_active:
        return
    
    try:
        # Sincronizar tableros
        if not sincronizar_tableros():
            print("Error en la sincronización. Cerrando juego.")
            return
        
        # Crear e inicializar tableros
        tablero_propio = crear_tablero()
        tablero_enemigo = crear_tablero()  # Vista del tablero enemigo
        colocar_barcos(tablero_propio)
        
        print("\nJuego iniciado!")
        print("Tu tablero:")
        imprimir_tablero(tablero_propio)
        
        # Determinar quién empieza (el servidor siempre va primero)
        mi_turno = is_server
        
        while game_active:
            if mi_turno:
                print("\n--- TU TURNO ---")
                print("Tablero enemigo (lo que conoces):")
                imprimir_tablero(tablero_enemigo)
                
                # Generar disparo automático
                x, y = generar_disparo_automatico()
                print(f"Disparando automáticamente en {x},{y}...")
                
                # Pausa para observar el juego
                time.sleep(TIEMPO_ENTRE_DISPAROS)
                
                # Enviar ataque
                respuesta = realizar_ataque_red(x, y)
                
                if "error" in respuesta:
                    if respuesta["error"] in ["conexion_perdida", "timeout"]:
                        print("Conexión perdida con el oponente")
                        return
                    elif respuesta["error"] == "coordenada_invalida":
                        print("Coordenada inválida")
                        continue
                
                # Procesar respuesta
                fila, columna = coordenada_a_indices(x, y)
                resultado = respuesta.get("resultado")
                
                # Actualizar IA con el resultado
                procesar_resultado_disparo(x, y, resultado)
                
                if resultado == "ya_disparado":
                    print("Ya habías disparado ahí")
                    continue
                elif resultado == "agua":
                    print(f"Disparaste en {x},{y} - ¡Agua!")
                    tablero_enemigo[fila][columna] = "-"
                    mi_turno = False
                elif resultado == "impacto":
                    print(f"Disparaste en {x},{y} - ¡Impacto!")
                    tablero_enemigo[fila][columna] = "T"
                    # Continúa siendo tu turno
                elif resultado == "hundido":
                    print(f"Disparaste en {x},{y} - ¡Hundido! ({respuesta.get('barco', 'Barco')})")
                    
                    # Marcar TODAS las posiciones del barco hundido en el tablero enemigo
                    posiciones = respuesta.get("posiciones", [(fila, columna)])
                    for f, c in posiciones:
                        tablero_enemigo[f][c] = "H"
                    
                    # Continúa siendo tu turno
                
                # Verificar victoria
                if respuesta.get("victoria"):
                    print("\n¡VICTORIA! Has hundido toda la flota enemiga!")
                    close_connection()
                    return
                    
            else:
                print("\n--- TURNO DEL OPONENTE ---")
                print("Esperando ataque...")
                
                # Recibir ataque
                ataque = receive_message()
                if not ataque:
                    print("El oponente se ha desconectado")
                    return
                
                x = ataque.get("x")
                y = ataque.get("y")
                
                # Procesar ataque
                respuesta = procesar_ataque_red(tablero_propio, x, y)
                
                # Enviar respuesta
                if not send_message(respuesta):
                    return
                
                # Mostrar resultado
                resultado = respuesta.get("resultado")
                if resultado == "agua":
                    print(f"Oponente disparó en {x},{y} - Agua")
                    mi_turno = True
                elif resultado == "impacto":
                    print(f"Oponente disparó en {x},{y} - Impacto en tu barco")
                    # Oponente continúa
                elif resultado == "hundido":
                    print(f"Oponente disparó en {x},{y} - Hundió tu {respuesta.get('barco', 'barco')}")
                    # Oponente continúa
                
                print("Tu tablero actualizado:")
                imprimir_tablero(tablero_propio)
                
                # Verificar derrota
                if respuesta.get("victoria"):
                    print("\n¡DERROTA! El oponente hundió toda tu flota!")
                    close_connection()
                    return
    
    except KeyboardInterrupt:
        print("\nJuego interrumpido por el usuario")
        close_connection()
    except Exception as e:
        print(f"Error durante el juego: {e}")
        close_connection()
    finally:
        # Asegurar que la conexión se cierre
        if connected:
            close_connection()
            
# FUNCIÓN PRINCIPAL
def main():
    """Función principal que inicia el juego"""
    try:
        juego_red()
    except KeyboardInterrupt:
        print("\n¡Hasta la próxima!")
    except Exception as e:
        print(f"Error crítico: {e}")

if __name__ == "__main__":
    main()