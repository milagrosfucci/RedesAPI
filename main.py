import json
import secrets
from collections import deque
from datetime import datetime, timedelta
from typing import Deque, Dict

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

# Esto evita que saturen el servidor. Usamos una "ventana de tiempo" 
# de 1 segundo y permitimos un maximo de 5 peticiones por IP en ese tiempo
VENTANA = timedelta(seconds=1)
MAX_PETICIONES = 5

# Este diccionario guarda las IPs que se conectan y la hora exacta de sus peticiones
cubos_ip: Dict[str, Deque[datetime]] = {}

# @app.middleware("http") hace que TODAS las peticiones pasen por acá primero antes de llegar a los GET/POST
@app.middleware("http")
async def limitador(request: Request, call_next):
    ip = request.client.host # Obtenemos la IP de quien hace la petición
    ahora = datetime.utcnow()
    cubo = cubos_ip.setdefault(ip, deque())

    # Borramos del registro las peticiones que ya son más viejas que 1 segundo
    while cubo and (ahora - cubo[0]) > VENTANA:
        cubo.popleft()

    # Si la IP ya hizo 5 peticiones en el ultimo segundo, le clavamos un error (Too Many Requests)
    if len(cubo) >= MAX_PETICIONES:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Demasiadas solicitudes: límite 5 req/s"}
        )

    # Si todo está bien, anotamos la peticion y dejamos que siga su curso
    cubo.append(ahora)
    return await call_next(request)


security = HTTPBasic()
USUARIOS: Dict[str, str] = {
    "admin": "redes2026",
    "valen": "redes2026",
    "mili": "redes2026"
}

# Esta funcion se va a ejecutar cada vez que alguien intente hacer un POST o DELETE
def verificar_credenciales(
    credenciales: HTTPBasicCredentials = Depends(security),
) -> str:
    # Buscamos si el usuario existe en nuestro diccionario USUARIOS
    pwd_correcta = USUARIOS[credenciales.username]
    
    # secrets.compare_digest es una forma segura de comparar contraseñas 
    if not pwd_correcta or not secrets.compare_digest(
        credenciales.password, pwd_correcta
    ):
        # Si la contraseña esta mal, devolvemos error (No autorizado)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credenciales.username  


# BaseModel para para obligar a que cuando nos manden un POST, la canción tenga 
# si o si todos estos campos y con el tipo de dato correcto (texto, entero, flotante)

class Cancion(BaseModel):
    genre: str
    artist_name: str
    track_name: str
    track_id: str
    popularity: int
    acousticness: float
    danceability: float
    duration_ms: int
    energy: float
    instrumentalness: float
    key: str
    liveness: float
    loudness: float
    mode: str
    speechiness: float
    tempo: float
    time_signature: str
    valence: float


# Una lee el archivo JSON y lo convierte a lista, y la otra guarda la lista devuelta al archivo
def cargar_datos():
    with open('spotify_150.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def guardar_datos(datos):
    with open('spotify_150.json', 'w', encoding='utf-8') as file:
        json.dump(datos, file, indent=4)


@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido a la API de Spotify - Proyecto Redes de Datos"}

@app.get("/canciones/buscar")
def buscar_por_artista(artista: str):
    datos = cargar_datos()
    resultado = []
    
    # para que la busqueda ignore si escriben en mayusculas o minúsculas
    for c in datos:
        if artista.lower() in str(c['artist_name']).lower(): 
            resultado.append(c)
    
    if resultado == []: 
        return {"error": "No se encontraron canciones del artista " + artista}
    
    return {"resultados_encontrados": len(resultado), "canciones": resultado}

@app.get("/canciones/populares")
def obtener_canciones_populares(min_popularidad: int = 15): 
    datos = cargar_datos()
    resultados = []
    
    # asume que es 15 por defecto.
    for c in datos:
        if int(c["popularity"]) >= min_popularidad:
            resultados.append(c)

    # sorted() y reverse=True ordenan las canciones de mayor a menor popularidad antes de devolverlas
    resultados_ordenados = sorted(resultados, key=lambda x: int(x["popularity"]), reverse=True)
    return {"filtro_popularidad": f"Mayor o igual a {min_popularidad}", "canciones": resultados_ordenados}

@app.get("/canciones/vibracion")
def buscar_por_vibracion(tipo: str):
    datos = cargar_datos()
    resultado = []
    
    # Arbitrariamente decidimos que más de 120 es alta vibración y menos es baja
    for c in datos:
        bpm = float(c['tempo'])
        if tipo.lower() == "alta" and bpm >= 120.0:
            resultado.append(c)
        elif tipo.lower() == "baja" and bpm < 120.0:
            resultado.append(c)
            
    if resultado == []:
        return {"error": "No se encontraron canciones con vibración: " + tipo}
        
    return {
        "vibracion_solicitada": tipo, 
        "cantidad_encontrada": len(resultado), 
        "canciones": resultado
    }


# "Depends(verificar_credenciales)", exige Autenticación Basic
@app.post("/canciones")
def agregar_cancion(cancion: Cancion, usuario: str = Depends(verificar_credenciales)):
    datos = cargar_datos()
    
    # Primero chequeamos que la canción no exista ya comparando el track_id.
    for c in datos:
        if c["track_id"] == cancion.track_id:
            raise HTTPException(status_code=400, detail="Esa canción ya existe en la base de datos")
            
    # cancion.model_dump() convierte nuestro modelo a un diccionario normal para poder guardarlo en el JSON
    datos.append(cancion.model_dump())
    guardar_datos(datos)
    
    return {"mensaje": "¡Canción agregada con éxito!", "autorizado_por": usuario, "cancion": cancion}

@app.delete("/canciones/{track_id}")
def borrar_cancion(track_id: str, usuario: str = Depends(verificar_credenciales)):
    datos = cargar_datos()
    
    # Usamos enumerate para saber en que posicion está la cancion cuando coincide el ID, la sacamos de la lista 
    for i, c in enumerate(datos):
        if c["track_id"] == track_id:
            cancion_borrada = datos.pop(i)
            guardar_datos(datos)
            return {"mensaje": "Canción eliminada", "autorizado_por": usuario, "cancion_borrada": cancion_borrada}
            
    # Si termina el bucle for y no encontró la canción, tira error 404
    raise HTTPException(status_code=404, detail="No se encontró la canción con ese ID")