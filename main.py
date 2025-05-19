import random
import sys

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
            orientacion = random.choice(['H', 'V'])  # Horizontal o Vertical
            
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
            if celda not in ("X", "-", "T", "H"):  # Si hay una letra de barco, aún quedan barcos
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
    posiciones = [(fila, columna)]
    
    # Verificar si hay partes del barco a la izquierda o derecha
    horizontal = (columna > 0 and (tablero[fila][columna-1] == letra_barco or tablero[fila][columna-1] == "T")) or \
                 (columna < TAMANIO_TABLERO-1 and (tablero[fila][columna+1] == letra_barco or tablero[fila][columna+1] == "T"))
    
    # Verificar si hay partes del barco arriba o abajo
    vertical = (fila > 0 and (tablero[fila-1][columna] == letra_barco or tablero[fila-1][columna] == "T")) or \
               (fila < TAMANIO_TABLERO-1 and (tablero[fila+1][columna] == letra_barco or tablero[fila+1][columna] == "T"))
    
    if not horizontal and not vertical:
        return posiciones
    
    if horizontal:
        c = columna - 1
        while c >= 0 and (tablero[fila][c] == letra_barco or tablero[fila][c] == "T"):
            posiciones.append((fila, c))
            c -= 1
        
        c = columna + 1
        while c < TAMANIO_TABLERO and (tablero[fila][c] == letra_barco or tablero[fila][c] == "T"):
            posiciones.append((fila, c))
            c += 1
    
    elif vertical:
        f = fila - 1
        while f >= 0 and (tablero[f][columna] == letra_barco or tablero[f][columna] == "T"):
            posiciones.append((f, columna))
            f -= 1
        
        f = fila + 1
        while f < TAMANIO_TABLERO and (tablero[f][columna] == letra_barco or tablero[f][columna] == "T"):
            posiciones.append((f, columna))
            f += 1
    
    return posiciones

def comprobar_hundido(tablero, letra_barco, fila, columna):
    """Comprueba si todas las partes de un barco específico han sido tocadas"""
    posiciones_barco = encontrar_todas_posiciones_barco(tablero, letra_barco, fila, columna)
    
    for f, c in posiciones_barco:
        if tablero[f][c] != "T":
            return False, posiciones_barco
    
    return True, posiciones_barco

def obtener_nombre_barco(letra_barco):
    """Devuelve el nombre completo del barco a partir de su letra inicial"""
    for nombre, _ in BARCOS.items():
        if nombre[0] == letra_barco:
            return nombre
    return None

# FUNCIONES DE DISPAROS
def disparar(tablero, tablero_vista, fila, columna):
    """Evalúa el disparo y devuelve el resultado: Agua, Tocado o Hundido"""
    if tablero_vista[fila][columna] in ("T", "H", "-"):
        print("Ya has disparado en esta posición. Intenta otra vez.")
        return None  
    
    if tablero[fila][columna] == "X":
        tablero[fila][columna] = "-"
        tablero_vista[fila][columna] = "-"
        return "Agua"

    letra_barco = tablero[fila][columna] 
    tablero[fila][columna] = "T" 
    tablero_vista[fila][columna] = "T" 
    
    hundido, posiciones = comprobar_hundido(tablero, letra_barco, fila, columna)
    
    if hundido:
        for f, c in posiciones:
            tablero[f][c] = "H"
            tablero_vista[f][c] = "H"
        
        nombre_barco = obtener_nombre_barco(letra_barco)
        if nombre_barco:
            return f"Hundido ({nombre_barco})"
        
        return "Hundido"
    
    return "Tocado"

# FUNCIONES DE ENTRADA
def entrada_usuario():
    """Solicita al usuario que ingrese una coordenada (letra y número) para disparar"""
    sys.stdout.write("Introduce la coordenada (ejemplo: A 5 o A5): ")
    sys.stdout.flush()
    entrada = sys.stdin.readline().strip().upper().replace(" ", "")

    try:
        if len(entrada) < 2:
            print("Formato incorrecto. Introduce una letra (A-J) seguida de un número (0-9).")
            return entrada_usuario()

        letra = entrada[0]
        columna_str = entrada[1:]
        
        if letra not in LETRAS_A_NUMEROS:
            print("Letra fuera de rango (A-J). Intenta de nuevo.")
            return entrada_usuario()
            
        fila = LETRAS_A_NUMEROS[letra]
        columna = int(columna_str)
        
        if 0 <= columna < 10:
            return fila, columna
        print("Columna fuera de rango (0-9). Intenta de nuevo.")
    except ValueError:
        print("Formato incorrecto. Introduce una letra (A-J) seguida de un número (0-9).")
    
    return entrada_usuario()

# FUNCIONES DE ESTADÍSTICAS
def mostrar_movimientos_totales(disparos_jugador, disparos_maquina):
    """Muestra el número total de movimientos realizados por el jugador y la máquina"""
    print("\nNÚMERO TOTAL DE MOVIMIENTOS:")
    print(f"Tus movimientos: {disparos_jugador}")
    print(f"Movimientos de la máquina: {disparos_maquina}")
    print(f"Total de movimientos en la partida: {disparos_jugador + disparos_maquina}")

def anuncia_ganador(jugador_gano, maquina_gano, disparos_jugador, disparos_maquina):
    """Anuncia el ganador del juego y muestra el conteo de movimientos"""
    if jugador_gano:
        print("\n¡Felicidades! Has hundido toda la flota enemiga. ¡Ganaste!")
        mostrar_movimientos_totales(disparos_jugador, disparos_maquina)
        return True
    elif maquina_gano:
        print("\nLa máquina ha hundido toda tu flota. ¡Perdiste!")
        mostrar_movimientos_totales(disparos_jugador, disparos_maquina)
        return True
    return False

# FUNCIONES DE TURNOS
def mostrar_estado_juego(tablero_jugador, tablero_vista_maquina, es_turno_jugador=True):
    """Muestra el estado actual del juego: primero el tablero del jugador, 
    luego si es turno del jugador, muestra el tablero enemigo"""
    print("\nTu tablero:")
    imprimir_tablero(tablero_jugador)
    
    if es_turno_jugador:
        print("\nTU TURNO")
        print("\nTablero enemigo (lo que has descubierto):")
        imprimir_tablero(tablero_vista_maquina)

def procesar_disparo_jugador(tablero_maquina, tablero_vista_maquina):
    """Procesa un disparo del jugador y devuelve el resultado"""
    fila, columna = entrada_usuario()
    resultado = disparar(tablero_maquina, tablero_vista_maquina, fila, columna)
    
    if resultado:
        letra_fila = NUMEROS_A_LETRAS[fila]
        print(f"Disparaste en {letra_fila}{columna} - Resultado: {resultado}")
        
        if resultado != "Agua":
            print("\nTablero enemigo actualizado:")
            imprimir_tablero(tablero_vista_maquina)
            
        return resultado, True
    
    return None, False

def turno_jugador(tablero_maquina, tablero_vista_maquina, tablero_jugador, disparos_jugador):
    """Permite al jugador realizar un disparo al tablero de la máquina"""
    mostrar_estado_juego(tablero_jugador, tablero_vista_maquina, True)
    
    seguir_disparando = True
    disparos_nuevos = 0
    
    while seguir_disparando:
        resultado, disparo_valido = procesar_disparo_jugador(tablero_maquina, tablero_vista_maquina)
        
        if disparo_valido:
            disparos_nuevos += 1
            
            if not quedan_barcos(tablero_maquina):
                return True, disparos_jugador + disparos_nuevos
                
            if resultado == "Agua":
                seguir_disparando = False
    
    return False, disparos_jugador + disparos_nuevos

def procesar_disparo_maquina(tablero_jugador):
    """Procesa un disparo de la máquina y devuelve el resultado"""
    fila = random.randint(0, TAMANIO_TABLERO - 1)
    columna = random.randint(0, TAMANIO_TABLERO - 1)
    
    resultado = disparar(tablero_jugador, tablero_jugador, fila, columna)
    
    if resultado:
        letra_fila = NUMEROS_A_LETRAS[fila]
        print(f"La máquina disparó en {letra_fila}{columna} - Resultado: {resultado}")
        
        if resultado != "Agua":
            print("\nTu tablero actualizado:")
            imprimir_tablero(tablero_jugador)
            
        return resultado, True
    
    return None, False

def turno_maquina(tablero_jugador, disparos_maquina):
    """Permite a la máquina realizar un disparo al tablero del jugador"""
    print("TURNO DE LA MÁQUINA")
    
    seguir_disparando = True
    disparos_nuevos = 0
    
    while seguir_disparando:
        resultado, disparo_valido = procesar_disparo_maquina(tablero_jugador)
        
        if disparo_valido:
            disparos_nuevos += 1
            
            if not quedan_barcos(tablero_jugador):
                return True, disparos_maquina + disparos_nuevos
                
            if resultado == "Agua":
                seguir_disparando = False
    
    return False, disparos_maquina + disparos_nuevos

# FUNCIONES DE FLUJO DE JUEGO
def inicializar_juego():
    """Inicializa los tableros y coloca los barcos"""
    # Crear tableros
    tablero_jugador = crear_tablero()
    tablero_maquina = crear_tablero()
    
    # Tablero de vista para la máquina (lo que ve el jugador)
    tablero_vista_maquina = crear_tablero()

    # Colocar barcos en los tableros
    colocar_barcos(tablero_jugador)
    colocar_barcos(tablero_maquina)
    
    return tablero_jugador, tablero_maquina, tablero_vista_maquina

def primer_turno_jugador(tablero_maquina, tablero_vista_maquina):
    """Gestiona el primer turno del jugador"""
    print("\nTU TURNO")
    print("\nTablero enemigo:")
    imprimir_tablero(tablero_vista_maquina)
    
    disparos_jugador = 0
    seguir_disparando = True
    jugador_gano = False
    
    while seguir_disparando:
        resultado, disparo_valido = procesar_disparo_jugador(tablero_maquina, tablero_vista_maquina)
        
        if disparo_valido:
            disparos_jugador += 1
            
            # Comprobar victoria
            if not quedan_barcos(tablero_maquina):
                jugador_gano = True
                break
                
            if resultado == "Agua":
                seguir_disparando = False  # Si es agua, termina el turno
    
    return jugador_gano, disparos_jugador

def ejecutar_partida():
    """Ejecuta el flujo principal de la partida"""
    # Inicialización
    tablero_jugador, tablero_maquina, tablero_vista_maquina = inicializar_juego()
    
    print("\n¡BIENVENIDO A HUNDIR LA FLOTA!")
    print("\nTu tablero inicial:")
    imprimir_tablero(tablero_jugador)
    
    # Contadores y estado del juego
    disparos_jugador = 0
    disparos_maquina = 0
    juego_terminado = False
    jugador_gano = False
    maquina_gano = False
    
    # Primer turno (especial)
    primer_turno = True
    
    while not juego_terminado:
        if primer_turno:
            # Gestionar el primer turno del jugador
            jugador_gano, disparos_primer_turno = primer_turno_jugador(tablero_maquina, tablero_vista_maquina)
            disparos_jugador += disparos_primer_turno
            primer_turno = False
        else:
            # Turno normal del jugador
            jugador_gano, disparos_jugador = turno_jugador(
                tablero_maquina, tablero_vista_maquina, tablero_jugador, disparos_jugador
            )

        # Verificar si el juego terminó después del turno del jugador
        if anuncia_ganador(jugador_gano, maquina_gano, disparos_jugador, disparos_maquina):
            juego_terminado = True
            continue
            
        # Turno de la máquina (solo si el jugador no ganó)
        if not jugador_gano:
            maquina_gano, disparos_maquina = turno_maquina(
                tablero_jugador, disparos_maquina
            )
            
            # Verificar si el juego terminó después del turno de la máquina
            if anuncia_ganador(jugador_gano, maquina_gano, disparos_jugador, disparos_maquina):
                juego_terminado = True

# FUNCIÓN PRINCIPAL
def main():
    """Función principal que inicia el juego"""
    ejecutar_partida()

if __name__ == "__main__":
    main()