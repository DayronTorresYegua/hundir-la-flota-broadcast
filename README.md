# Hundir la Flota 

## Características

- **Juego completamente automático**: Los disparos se realizan mediante IA inteligente
- **Conexión automática**: Los jugadores se encuentran automáticamente en la red local
- **Sincronización en tiempo real**: Los tableros se actualizan automáticamente entre jugadores

## Requisitos

- Python instalado
- Dos computadoras en la misma red local
- Puertos 6969 y 7171 disponibles

## Instalación

1. Descarga el archivo `main.py`
2. No requiere librerías adicionales (usa solo librerías estándar de Python)

## Ejecución

### Opción 1: Ejecutar en ambas computadoras simultáneamente
```bash
python main.py
```

### Opción 2: Ejecutar primero en una computadora, luego en la otra
```bash
python main.py
```

## Cómo funciona

1. **Búsqueda automática**: Al ejecutar, el programa busca automáticamente otros jugadores en la red
2. **Conexión automática**: Se establece conexión cuando encuentra otro jugador
3. **Colocación de barcos**: Los barcos se colocan aleatoriamente en cada tablero
4. **Juego automático**: Los disparos se realizan automáticamente usando IA
5. **Finalización**: El juego termina cuando uno de los jugadores hunde toda la flota enemiga

## Barcos incluidos

- Portaaviones (4 casillas)
- Buque (3 casillas)  
- Crucero (2 casillas)
- Submarino (2 casillas)
- Lancha (1 casilla)

## Controles

- **Ctrl+C**: Salir del juego en cualquier momento
- El juego es completamente automático, solo observa cómo se desarrolla

## Configuración de red

- **Puerto de búsqueda**: 6969
- **Puerto de juego**: 7171
- **Timeout por turno**: 30 segundos
- **Tiempo entre disparos**: 2 segundos

## Solución de problemas

- **Error de puerto bloqueado**: Verifica que tu firewall permita los puertos 6969 y 7171
- **No encuentra jugadores**: Asegúrate de que ambas computadoras estén en la misma red local
- **Conexión perdida**: El juego se cierra automáticamente si se pierde la conexión
