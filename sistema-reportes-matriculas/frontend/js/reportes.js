document.addEventListener('DOMContentLoaded', () => {
    // El evento DOMContentLoaded asegura que el script se ejecuta una vez que el HTML está completamente cargado.

    // Define la dirección IP del servidor donde se ejecuta FastAPI (Backend).
    const SERVER_IP = '192.168.100.132'; 
    // Construye la URL completa del endpoint de la API para obtener los reportes.
    const API_ENDPOINT = `http://${SERVER_IP}:8000/reportes/`;
    
    // Obtiene referencias a los elementos clave del Document Object Model (DOM).
    const reportList = document.getElementById('report-list');
    const loadingMessage = document.getElementById('loading-message');

    // Función asíncrona para obtener los datos de los reportes desde el servidor.
    async function fetchReportes() {
        loadingMessage.textContent = 'Cargando datos...';
        
        try {
            // Realiza la solicitud GET asíncrona al endpoint de la API.
            const response = await fetch(API_ENDPOINT);
            // Parsea la respuesta del servidor como un objeto JSON.
            const result = await response.json();

            // Oculta el mensaje de carga tras recibir la respuesta.
            loadingMessage.classList.add('hidden');

            // Verifica si la respuesta HTTP es exitosa (código 200-299) y el estado lógico es 'success'.
            if (response.ok && result.status === 'success') {
                // Llama a la función para renderizar la lista de reportes.
                displayReportes(result.data);
            } else {
                // Muestra un mensaje de error si la conexión fue exitosa pero el servidor reportó un fallo lógico.
                reportList.innerHTML = `<p class="error">Error al cargar reportes: ${result.detail || result.mensaje}</p>`;
            }

        } catch (error) {
            // Captura errores de red (ej. si el servidor está apagado o la IP es inaccesible).
            loadingMessage.classList.remove('hidden');
            loadingMessage.textContent = `Error de conexión: Asegúrate de que FastAPI esté corriendo en ${SERVER_IP}:8000.`;
            // Limpia la lista de reportes ante un fallo de conexión.
            reportList.innerHTML = '';
        }
    }

    // Función que toma el array de reportes y los renderiza en la interfaz.
    function displayReportes(reportes) {
        // Maneja el caso en que la base de datos no tenga registros.
        if (reportes.length === 0) {
            reportList.innerHTML = `<p>No hay reportes registrados aún.</p>`;
            return;
        }

        // Itera sobre cada objeto de reporte para crear su representación visual.
        reportes.forEach(reporte => {
            // Extrae el nombre del propietario anidado bajo la clave 'propietario_id' (relación Supabase).
            // Si la placa no se encontró, la relación es NULL, y se asigna un mensaje por defecto.
            const propietarioNombre = reporte.propietario_id ? reporte.propietario_id.nombre_completo : 'Propietario No Registrado';
            
            // Crea un nuevo elemento div para contener la tarjeta de reporte.
            const reporteElement = document.createElement('div');
            reporteElement.className = 'report-card';
            
            // Define el contenido HTML de la tarjeta de reporte.
            reporteElement.innerHTML = `
                <h3>Placa Detectada: **${reporte.placa_detectada}**</h3>
                <p><strong>Propietario:</strong> ${propietarioNombre}</p>
                <p><strong>Fecha:</strong> ${new Date(reporte.fecha_reporte).toLocaleString()}</p>
                <p><strong>Descripción:</strong> ${reporte.descripcion}</p>
                <p class="image-links">
                    <a href="${reporte.url_foto_placa}" target="_blank">Ver Placa</a> | 
                    <a href="${reporte.url_foto_infraccion}" target="_blank">Ver Infracción</a>
                </p>
                <hr>
            `;
            // Añade el elemento de reporte al contenedor principal en el DOM.
            reportList.appendChild(reporteElement);
        });
    }

    // Llama a la función principal para iniciar la carga de datos al cargar la página.
    fetchReportes();
    // Nota: El registro del Service Worker se maneja en el archivo principal (script.js) para la funcionalidad de la PWA.
});