import json
from fastapi import FastAPI

app = FastAPI()

def cargar_datos():
    with open('spotify_150.json', 'r', encoding='utf-8') as file:
        return json.load(file)

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