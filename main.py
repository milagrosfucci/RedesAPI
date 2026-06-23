import json
import secrets  # <-- De los profes: Para comparar credenciales de forma segura
from typing import Dict
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel  # <-- Para la validación estricta en el POST

app = FastAPI()


security = HTTPBasic()

USUARIOS: Dict[str, str] = {
    "admin": "redes2026",
    "valen": "redes2026",
    "mili": "redes2026"
}

def verificar_credenciales(
    credenciales: HTTPBasicCredentials = Depends(security),
) -> str:
    pwd_correcta = USUARIOS.get(credenciales.username)
    if not pwd_correcta or not secrets.compare_digest(
        credenciales.password, pwd_correcta
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credenciales.username  


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


def cargar_datos():
    with open('spotify_150.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def guardar_datos(datos):
    with open('spotify_150.json', 'w', encoding='utf-8') as file:
        json.dump(datos, file, indent=4)


@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido a la API de Spotify - Proyecto Redes de Datos"}

# Búsqueda por Artista
# Ejemplo de uso: /canciones/buscar?artista=Queen
@app.get("/canciones/buscar")
def buscar_por_artista(artista: str):
    datos = cargar_datos()
    resultado = []
    # filtramos la lista buscando coincidencias 
    for c in datos:
        if artista.lower() in str(c['artist_name']).lower(): # ignoramos las mayusculas
            resultado.append(c)
    
    if resultado == []: # no hay resultados
        return {"No se encontraron canciones del artista" + artista}
    
    return {"resultados_encontrados": len(resultado), "canciones": resultado}

# Filtrar por Nivel de Popularidad (
# Ejemplo de uso: /canciones/populares?min_popularidad=80
@app.get("/canciones/populares")
def obtener_canciones_populares(min_popularidad: int = 15): # 15 es el valor por defecto si el usuario no manda nada
    datos = cargar_datos()
    resultados = []
    for c in datos:
        if int(c["popularity"]) >= min_popularidad:
            resultados.append(c)

    # Ordenamos de mayor a menor popularidad
    resultados_ordenados = sorted(resultados, key=lambda x: int(x["popularity"]), reverse=True)
    
    return {"filtro_popularidad": f"Mayor o igual a {min_popularidad}", "canciones": resultados_ordenados}

# Buscar canciones por su vibración/ritmo (ej: /canciones/vibracion?tipo=alta)
@app.get("/canciones/vibracion")
def buscar_por_vibracion(tipo: str):
    datos = cargar_datos()
    resultado = []
    
    for c in datos:
        # Convertimos el tempo a número flotante porque en el JSON viene con decimales
        bpm = float(c['tempo'])
        
        # Si pide vibración ALTA, buscamos canciones movidas (más de 120 BPM)
        if tipo.lower() == "alta" and bpm >= 120.0:
            resultado.append(c)
            
        # Si pide vibración BAJA, buscamos canciones tranqui (menos de 120 BPM)
        elif tipo.lower() == "baja" and bpm < 120.0:
            resultado.append(c)
            
    if resultado == []:
        return {"No se encontraron canciones con vibración:" + tipo}
        
    return {
        "vibracion_solicitada": tipo, 
        "cantidad_encontrada": len(resultado), 
        "canciones": resultado
    }


@app.post("/canciones")
def agregar_cancion(cancion: Cancion, usuario: str = Depends(verificar_credenciales)):
    datos = cargar_datos()
    
    for c in datos:
        if c.get("track_id") == cancion.track_id:
            raise HTTPException(status_code=400, detail="Esa canción ya existe en la base de datos")
            
    datos.append(cancion.model_dump())
    guardar_datos(datos)
    
    return {"mensaje": "¡Canción agregada con éxito!", "autorizado_por": usuario, "cancion": cancion}

@app.delete("/canciones/{track_id}")
def borrar_cancion(track_id: str, usuario: str = Depends(verificar_credenciales)):
    datos = cargar_datos()
    
    for i, c in enumerate(datos):
        if c.get("track_id") == track_id:
            cancion_borrada = datos.pop(i)
            guardar_datos(datos)
            return {"mensaje": "Canción eliminada", "autorizado_por": usuario, "cancion_borrada": cancion_borrada}
            
    raise HTTPException(status_code=404, detail="No se encontró la canción con ese ID")