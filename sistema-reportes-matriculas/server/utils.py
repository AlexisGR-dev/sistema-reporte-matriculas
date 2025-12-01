import smtplib
import ssl
import requests
import re # Módulo para expresiones regulares (aunque no se usa directamente, es útil para limpiar texto)
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Importa las credenciales y configuración desde el módulo local 'config'
from config import (
    SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY, # Claves de conexión y servicio de Supabase
    EMAIL_ADDRESS, EMAIL_PASSWORD, # Credenciales del remitente del correo
    SMTP_SERVER, SMTP_PORT # Configuración del servidor de correo SMTP
)

# --- 1. FUNCIÓN DE LIMPIEZA Y NORMALIZACIÓN DE placa ---
def limpiar_y_normalizar_placa(raw_text: str) -> str:
    """
    Limpia el texto detectado por OCR para que se ajuste al formato de matrícula
    (alfanumérico) y corrige errores comunes de EasyOCR.
    """
    # Verifica si la entrada de texto está vacía o es nula
    if not raw_text:
        return ""
        
    # Convierte el texto detectado a mayúsculas para estandarizar
    raw_placa = raw_text.upper()
    
    # Define un mapeo de caracteres incorrectos o ambiguos a su forma alfanumérica correcta
    replacements = {
        '¢': 'C', '£': 'E', '|': 'I', '/': '1'
    }
    
    cleaned_placa = ""
    # Itera sobre cada carácter de la placa cruda
    for char in raw_placa:
        # Elimina espacios y guiones intermedios
        char = char.replace(" ", "").replace("-", "")
        
        # Aplica correcciones definidas en el diccionario 'replacements'
        char = replacements.get(char, char)
        
        # Filtrar: Solo acepta caracteres que son letras o números (alfanuméricos)
        if char.isalnum():
            cleaned_placa += char
            
    return cleaned_placa

# --- 2. FUNCIÓN DE BÚSQUEDA EN SUPABASE ---
def buscar_propietario_por_placa(placa_detectada: str):
    """
    Consulta Supabase usando la vista 'reporte_datos_view' para obtener 
    el propietario_id, email y nombre completo asociados a una placa.
    """
    # Se utiliza la clave ANON para las operaciones de lectura
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    # Construye la consulta REST: busca por la columna 'placa' e incluye las columnas requeridas
    query = f"placa=eq.{placa_detectada}&select=propietario_id,email,nombre_completo"
    
    try:
        # Envía la solicitud GET a la API REST de Supabase
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/reporte_datos_view?{query}",
            headers=headers,
            timeout=5 # Límite de tiempo para la respuesta de la base de datos
        )
        # Lanza una excepción si el código de estado es 4xx o 5xx (error de cliente/servidor)
        response.raise_for_status() 
        # Devuelve la respuesta JSON con los datos del propietario
        return response.json()
    except requests.exceptions.RequestException as e:
        # Captura errores de conexión o errores HTTP
        print(f"ERROR de Supabase o red: {e}")
        return None

# --- 3. FUNCIÓN DE ENVÍO DE CORREO ---
def enviar_notificacion(destinatario_email: str, placa: str, descripcion: str) -> bool:
    """
    Envía la notificación por correo electrónico al propietario utilizando SMTP seguro (SSL/TLS).
    """
    # 1. Configuración del mensaje
    # Crea un objeto multipart para permitir contenido HTML
    message = MIMEMultipart("alternative")
    message["Subject"] = f"Notificación de Infracción Detectada: placa {placa}"
    message["From"] = EMAIL_ADDRESS
    message["To"] = destinatario_email

    # Contenido del cuerpo del mensaje en formato HTML
    html = f"""\
    <html>
      <body>
        <p>Estimado propietario,</p>
        <p>Se ha detectado una infracción de tránsito asociada a la placa **{placa}**.</p>
        <p><strong>Detalles del Reporte:</strong></p>
        <ul>
          <li><strong>placa:</strong> {placa}</li>
          <li><strong>Descripción de la Infracción:</strong> {descripcion}</li>
        </ul>
        <p>Por favor, tome las medidas necesarias. Este es un sistema de notificación automatizado.</p>
        <p>Atentamente,<br>El Sistema de Monitoreo de Tránsito</p>
      </body>
    </html>
    """
    
    # Adjunta el contenido HTML al mensaje
    part1 = MIMEText(html, "html")
    message.attach(part1)

    # 2. Envío del correo
    # Crea un contexto SSL para la conexión segura
    context = ssl.create_default_context()
    try:
        # Establece la conexión segura con el servidor SMTP
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            # Inicia sesión con las credenciales del remitente (clave de aplicación)
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            # Envía el correo electrónico
            server.sendmail(EMAIL_ADDRESS, destinatario_email, message.as_string())
        return True
    except Exception as e:
        # Captura cualquier error durante el proceso de envío
        print(f"ERROR al enviar correo: {e}")
        return False
    
# --- 4. FUNCIÓN PARA SUBIR ARCHIVOS AL STORAGE ---
def subir_archivo_a_supabase(file_content: bytes, file_name: str, bucket_name: str) -> str | None:
    """Sube el contenido binario de un archivo al Storage de Supabase."""
    
    # Construye la URL del endpoint de Storage (usa el nombre del bucket y del archivo)
    storage_url = f"{SUPABASE_URL}/storage/v1/object/{bucket_name}/{file_name}"
    
    # Se utiliza la clave SERVICE_ROLE para operaciones de escritura en Storage
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "image/jpeg" # Define el tipo de contenido que se está enviando
    }
    
    try:
        # Envía una solicitud POST con el contenido binario del archivo
        response = requests.post(
            storage_url, 
            headers=headers, 
            data=file_content # El contenido binario del archivo leído en memoria
        )
        response.raise_for_status() 

        # Devuelve la URL pública para acceder al archivo subido
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{file_name}"
        return public_url
        
    except requests.exceptions.RequestException as e:
        # Captura y registra errores de conexión o errores de la API de Storage
        print(f"ERROR al subir archivo a Storage: {e}")
        return None

# --- 5. FUNCIÓN PARA GUARDAR REPORTE EN LA BASE DE DATOS ---
def registrar_reporte_db(report_data: dict) -> bool:
    """Inserta el reporte con las URLs de las fotos en la tabla 'reportes'."""
    
    # Se utiliza la clave SERVICE_ROLE para operaciones de escritura (INSERT)
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Envía la solicitud POST al endpoint REST de la tabla 'reportes' (en minúsculas)
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/reportes",
            headers=headers,
            json=report_data
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        # Captura y registra errores de inserción
        print(f"ERROR al registrar el reporte en la tabla Reportes: {e}")
        return False

# --- 6. FUNCIÓN PARA OBTENER TODOS LOS REPORTES ---
def obtener_todos_los_reportes():
    """Obtiene todos los registros de la tabla Reportes, incluyendo el nombre del propietario unido."""
    
    # Se utiliza la clave ANON para las operaciones de lectura
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    # Construye la consulta: selecciona todos los campos (*) y anida el nombre completo 
    # usando la clave foránea 'propietario_id'. Ordena por fecha de reporte descendente.
    query = "select=*,propietario_id(nombre_completo)&order=fecha_reporte.desc"
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/reportes?{query}",
            headers=headers
        )
        response.raise_for_status()
        # Devuelve la lista de reportes en formato JSON
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERROR al obtener reportes de la DB: {e}")
        return None