from fastapi import (
    # FastAPI es la clase principal del framework
    FastAPI,
    # File se usa para declarar que un parámetro de endpoint es un archivo subido
    File,
    # UploadFile maneja el archivo subido de forma asíncrona
    UploadFile,
    # Form se usa para declarar campos de texto dentro de un formulario multipart
    Form,
    # HTTPException se usa para devolver errores HTTP estándar al cliente
    HTTPException
)
from fastapi.middleware.cors import CORSMiddleware
# uvicorn es el servidor ASGI que ejecuta la aplicación FastAPI
import uvicorn
# easyocr es la librería de reconocimiento óptico de caracteres
import easyocr
# shutil se usa para operaciones de alto nivel con archivos (como copiar/mover)
import shutil
# os se usa para interactuar con el sistema operativo (directorios, rutas, archivos)
import os
# time se usa para medir el tiempo y generar timestamps únicos
import time

# Importación de todas las funciones de lógica de negocio desde el módulo utils
from utils import (
    enviar_notificacion,
    buscar_propietario_por_placa,
    limpiar_y_normalizar_placa,
    subir_archivo_a_supabase, 
    registrar_reporte_db,
    obtener_todos_los_reportes
)

# --- CONFIGURACIÓN E INICIALIZACIÓN ---

# Inicializa la aplicación FastAPI
app = FastAPI()

# Inicializa easyOCR (solo una vez) al inicio del servidor
try:
    # Se crea el lector, especificando el idioma (español) y usando la CPU (gpu=False)
    reader = easyocr.Reader(['es',], gpu=False) 
except Exception as e:
    # Registra un error si el lector no se pudo inicializar (por ejemplo, por archivos faltantes)
    print(f"Error al inicializar EasyOCR: {e}")
    # El lector se mantiene como None, lo cual será comprobado en el endpoint

# Configuración CORS (Cross-Origin Resource Sharing)
# Esto permite que el frontend (ejecutándose en un puerto o IP diferente)
# pueda comunicarse con la API.
app.add_middleware(
    CORSMiddleware,
    # Se permite cualquier origen para el entorno de desarrollo ("*")
    allow_origins=["*"], 
    allow_credentials=True,
    # Se permiten todos los métodos HTTP (POST, GET, etc.)
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENDPOINT PRINCIPAL (REPORTE DE INFRACCIÓN) ---

# Define la ruta POST para recibir los datos del formulario del cliente
@app.post("/reportar-infraccion/")
async def reportar_infraccion(
    # Parámetros esperados del formulario multipart:
    placa_foto: UploadFile = File(...),      # Foto de la matrícula como archivo
    infraccion_foto: UploadFile = File(...), # Foto general de la infracción como archivo
    descripcion: str = Form(...)             # Descripción del problema como texto
):
    # Registra el tiempo de inicio para medir la duración de la solicitud
    start_time = time.time()
    # Imprime un log en la consola del servidor al recibir una nueva petición
    print(f"\n--- NUEVO REPORTE RECIBIDO ({time.ctime()}) ---")
    print(f"INFO: Descripción recibida: {descripcion[:50]}...")

    # Verifica si el lector OCR se inicializó correctamente
    if reader is None:
        # Si falla, devuelve un error 500 al cliente
        raise HTTPException(status_code=500, detail="El lector OCR no está inicializado.")

    # 1. LECTURA DE ARCHIVOS DE ENTRADA Y CREACIÓN DE ARCHIVO TEMPORAL
    
    # Lee el contenido binario de las imágenes en la memoria RAM
    placa_content = await placa_foto.read()
    infraccion_content = await infraccion_foto.read()
    
    # Crea un directorio temporal si no existe para guardar el archivo de la matrícula
    os.makedirs("temp", exist_ok=True)
    placa_path = os.path.join("temp", placa_foto.filename)
    
    # Inicializa variables que serán usadas dentro y fuera del bloque try
    vehiculos = None
    propietario_id = None
    placa_detectada = None
    
    try:
        # 2. GUARDAR TEMPORAL Y EJECUTAR OCR
        
        # Abre el archivo temporal en modo escritura binaria ('wb')
        with open(placa_path, "wb") as buffer:
            # Escribe el contenido de la matrícula en el disco (necesario para EasyOCR)
            buffer.write(placa_content) 
            
        # Ejecuta el reconocimiento óptico de caracteres (OCR) en la imagen de la placa
        results = reader.readtext(placa_path, detail=0)
        
        # Evalúa el resultado del OCR
        if not results:
            # Si no se detecta texto, se marca la placa como no detectada
            placa_detectada = "NO_DETECTADA"
            print("No se detectó texto en la imagen.")
        else:
            # Toma el primer resultado detectado y lo limpia usando la función auxiliar
            raw_text = results[0]
            placa_detectada = limpiar_y_normalizar_placa(raw_text)
        
        print(f"Placa detectada: {placa_detectada}")

        # 3. BÚSQUEDA EN SUPABASE (Obtener Propietario ID y Email)
        # Solo procede con la búsqueda si el OCR detectó algo
        if placa_detectada != "NO_DETECTADA":
            # Llama a la función que consulta la base de datos por la placa
            vehiculos = buscar_propietario_por_placa(placa_detectada)
        
        # Procesa el resultado de la búsqueda
        if vehiculos:
            # Extrae el ID, el email y el nombre del propietario de los resultados
            propietario_id = vehiculos[0].get("propietario_id") 
            destinatario_email = vehiculos[0]["email"]
            propietario_nombre = vehiculos[0]["nombre_completo"]
            print(f"DB: Propietario encontrado: ID = {propietario_id} |Nombre={propietario_nombre} | Email={destinatario_email}")
        else:
            # Si no se encuentra, las variables se mantienen como None
            propietario_id = None 
            destinatario_email = None
            print(f"DB: Propietario NO encontrado para placa: {placa_detectada}")
        
        # 4. SUBIDA DE IMÁGENES A SUPABASE STORAGE
        
        # Genera un timestamp único para nombrar los archivos
        timestamp = int(time.time())
        # Crea nombres de archivo basados en la placa detectada y el timestamp
        placa_name = f"{placa_detectada}_{timestamp}_placa.jpg"
        infraccion_name = f"{placa_detectada}_{timestamp}_infraccion.jpg"

        print(f"STORAGE: Subiendo evidencia. Nombres: {placa_name} y {infraccion_name}")
        
        # Llama a la función que sube el contenido binario (leído en memoria) al Storage
        url_placa = subir_archivo_a_supabase(placa_content, placa_name, bucket_name="reportes-evidencia")
        url_infraccion = subir_archivo_a_supabase(infraccion_content, infraccion_name, bucket_name="reportes-evidencia")
        
        # Verifica que ambas subidas hayan sido exitosas
        if not url_placa or not url_infraccion:
            # Si falla, devuelve un error 500
            raise HTTPException(status_code=500, detail="Fallo al subir imágenes de evidencia a Storage.")
        
        # 5. REGISTRAR REPORTE EN LA TABLA 'Reportes'
        
        reporte_data = {
            # El ID será NULL si no se encontró un propietario
            "propietario_id": propietario_id, 
            "placa_detectada": placa_detectada,
            "descripcion": descripcion,
            "url_foto_placa": url_placa,
            "url_foto_infraccion": url_infraccion
        }
        print("DB: Intentando registrar el reporte en la tabla 'reportes'...")
        # Llama a la función que inserta el registro en la base de datos
        if not registrar_reporte_db(reporte_data):
            # Si falla, registra una advertencia en la consola
            print("ADVERTENCIA: Fallo al guardar el registro en la tabla Reportes.")

        # 6. ENVÍO DE CORREO Y RESPUESTA FINAL
        
        if destinatario_email:
            # Si se encontró un email, se procede a enviar la notificación
            email_success = enviar_notificacion(
                destinatario_email=destinatario_email, 
                placa=placa_detectada, 
                descripcion=descripcion
            )
            
            # Formatea la respuesta al cliente basada en el éxito del envío
            if email_success:
                mensaje = f"Reporte enviado con éxito a {destinatario_email}."
                status_code = "success"
            else:
                mensaje = f"Placa encontrada, pero falló el envío del correo."
                status_code = "error"
        else:
            # Si no hay email, se confirma el registro del reporte
            mensaje = "Reporte guardado con éxito. No se encontró propietario asociado para notificar."
            status_code = "warning"
            
        # Devuelve la respuesta final al frontend
        return {"status": status_code, "placa_detectada": placa_detectada, "mensaje": mensaje}

    except HTTPException:
        # Relanza cualquier error HTTPException que haya ocurrido previamente
        raise
    except Exception as e:
        # Captura y maneja cualquier error no esperado
        print(f"ERROR INESPERADO: {e}")
        # Devuelve un error 500 genérico
        raise HTTPException(status_code=500, detail=f"Ocurrió un error interno: {e}")

    finally:
        # 7. Limpieza: Este bloque siempre se ejecuta, incluso si hay excepciones
        # Asegura que el archivo temporal usado para el OCR sea eliminado
        if os.path.exists(placa_path):
            os.remove(placa_path)

# --- ENDPOINT DE LECTURA (LISTA DE REPORTES) ---

# Define la ruta GET para obtener el listado completo de reportes
@app.get("/reportes/")
def obtener_reportes():
    """Devuelve la lista de reportes desde Supabase."""
    
    # Llama a la función auxiliar para obtener todos los registros
    reportes = obtener_todos_los_reportes()
    
    # Manejo de errores de conexión con la base de datos
    if reportes is None:
        raise HTTPException(status_code=500, detail="Fallo al conectar con la base de datos para obtener reportes.")
    
    # Manejo de caso sin resultados
    if not reportes:
        return {"status": "success", "data": [], "mensaje": "No hay reportes registrados."}
        
    # Devuelve los datos obtenidos en formato JSON
    return {"status": "success", "data": reportes}

# --- EJECUCIÓN DEL SERVIDOR ---

if __name__ == "__main__":
    # Inicia el servidor Uvicorn en la interfaz de red 0.0.0.0 (accesible localmente y en red)
    # en el puerto 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)