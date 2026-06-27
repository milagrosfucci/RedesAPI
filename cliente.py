import requests

#'127.0.0.1' es la dirección de "localhost"
# se debe cambiar por la dirección IP de la computadora que hace de Servidor
URL_BASE = "http://127.0.0.1:8001"

def menu():
    print("\n--- Cliente API Spotify ---")
    print("1. Buscar por artista (GET)")
    print("2. Filtrar por popularidad (GET)")
    print("3. Filtrar por vibracion (GET)")
    print("4. Agregar cancion (POST)")
    print("5. Eliminar cancion (DELETE)")
    print("6. Salir")
    return input("Seleccione una opcion: ")

def main():
    print(f"Iniciando cliente. Conectando a {URL_BASE}...")
    
    while True:
        opcion = menu()
        
        if opcion == '1':
            artista = input("Ingrese el artista a buscar: ")
            try:
                # requests.get envía una petición HTTP GET
                # El parámetro 'params' agrega automáticamente las variables a la URL 
                # (ejemplo: /canciones/buscar?artista=Queen)
                res = requests.get(f"{URL_BASE}/canciones/buscar", params={"artista": artista})
                
                # Verificamos que el status_code sea 200 (OK)
                if res.status_code == 200:
                    # res.json() convierte el texto recibido del servidor a un diccionario de Python
                    datos = res.json()
                    if "error" in datos:
                        print(datos["error"])
                    else:
                        print(f"Resultados ({datos['resultados_encontrados']}):")
                        for i, c in enumerate(datos['canciones'], 1):
                            print(f" {i}. {c['track_name']} - {c['artist_name']}")
                else:
                    print(f"Error HTTP: {res.status_code}")
            except requests.exceptions.RequestException:
                # Atrapamos errores de red por si el servidor esta apagado
                print("Error de conexion con el servidor.")

        elif opcion == '2':
                top = input("Cantidad de canciones del top a mostrar (ej. 10): ")
                # Si el usuario no ingresa un número, enviamos 10 por defecto
                top = int(top) if top.isdigit() else 10
            
                try:
                # Enviamos el parametro 'top' en lugar de 'min_popularidad'
                    res = requests.get(f"{URL_BASE}/canciones/populares", params={"top": top})
                
                    if res.status_code == 200:
                        datos = res.json()
                        print(f"Top {top} de canciones:")
                        for i, c in enumerate(datos.get('canciones', []), 1):
                            print(f" {i}. {c['track_name']} (Popularidad: {c.get('popularity', 0)})")
                    else:
                        print(f"Error HTTP: {res.status_code}")
                except requests.exceptions.RequestException:
                    print("Error de conexion con el servidor.")

        elif opcion == '3':
            tipo = input("Tipo de vibracion ('alta' o 'baja'): ")
            try:
                res = requests.get(f"{URL_BASE}/canciones/vibracion", params={"tipo": tipo})
                if res.status_code == 200:
                    datos = res.json()
                    if "error" in datos:
                        print(datos["error"])
                    else:
                        print(f"Canciones de vibracion {tipo}:")
                        for i, c in enumerate(datos['canciones'], 1):
                            print(f" {i}. {c['track_name']} (Tempo: {c['tempo']})")
                else:
                    print(f"Error HTTP: {res.status_code}")
            except requests.exceptions.RequestException:
                print("Error de conexion con el servidor.")

        elif opcion == '4':
            print("--- Ingreso de nueva cancion ---")
            track_id = input("ID de cancion: ")
            track_name = input("Nombre de la cancion: ")
            artist_name = input("Nombre del artista: ")
            genre = input("Genero: ")
            popularity = input("Popularidad (0-100): ")
            
            usuario = input("Usuario autorizado: ")
            clave = input("Contrasena: ")
            
            nueva_cancion = {
                "genre": genre,
                "artist_name": artist_name,
                "track_name": track_name,
                "track_id": track_id,
                "popularity": int(popularity) if popularity.isdigit() else 50,
                "acousticness": 0.5, "danceability": 0.5, "duration_ms": 200000,
                "energy": 0.5, "instrumentalness": 0.0, "key": "C",
                "liveness": 0.1, "loudness": -5.0, "mode": "Major",
                "speechiness": 0.05, "tempo": 120.0, "time_signature": "4/4",
                "valence": 0.5
            }
            
            try:
                #  requests.post envía una petición para modificar datos
                # 'json=nueva_cancion' envía el diccionario empaquetado en formato JSON en el cuerpo del mensaje
                # 'auth=(usuario, clave)' envía las credenciales 
                res = requests.post(f"{URL_BASE}/canciones", json=nueva_cancion, auth=(usuario, clave))
                if res.status_code == 200:
                    print("Cancion agregada con exito.")
                elif res.status_code == 401:
                    print("Error 401: Credenciales incorrectas.")
                elif res.status_code == 429:
                    print("Error 429: Limite de solicitudes alcanzado (Rate Limit).")
                else:
                    print(f"Error: {res.json().get('detail', res.status_code)}")
            except requests.exceptions.RequestException:
                print("Error de conexion con el servidor.")

        elif opcion == '5':
            track_id = input("Ingrese el ID de la cancion a borrar: ")
            usuario = input("Usuario autorizado: ")
            clave = input("Contrasena: ")
            
            try:
                # requests.delete envía la petición de borrado a la URL específica con el ID
                res = requests.delete(f"{URL_BASE}/canciones/{track_id}", auth=(usuario, clave))
                if res.status_code == 200:
                    print("Cancion eliminada correctamente.")
                elif res.status_code == 401:
                    print("Error 401: Credenciales incorrectas.")
                elif res.status_code == 404:
                    print("Error 404: Cancion no encontrada.")
                elif res.status_code == 429:
                    print("Error 429: Limite de solicitudes alcanzado.")
                else:
                    print(f"Error HTTP: {res.status_code}")
            except requests.exceptions.RequestException:
                print("Error de conexion con el servidor.")

        elif opcion == '6':
            print("Saliendo del cliente.")
            break
            
        else:
            print("Opcion invalida.")

if __name__ == "__main__":
    main()