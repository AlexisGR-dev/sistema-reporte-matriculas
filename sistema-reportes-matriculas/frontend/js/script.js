document.addEventListener('DOMContentLoaded', () => {
    // El evento DOMContentLoaded asegura que el script se ejecuta una vez que el HTML está completamente cargado.

    // Define las constantes de conexión al servidor FastAPI (Backend)
    // La IP debe coincidir con la dirección local del PC que ejecuta el servidor (Entorno de desarrollo).
    const SERVER_IP = '192.168.100.132'; 
    const SERVER_PORT = '8000';
    // URL completa del endpoint de la API para enviar el reporte
    const API_ENDPOINT = `http://${SERVER_IP}:${SERVER_PORT}/reportar-infraccion/`;

    // Obtiene referencias a los elementos clave del Document Object Model (DOM)
    const form = document.getElementById('reporteForm');
    const submitButton = document.getElementById('submitButton');
    const statusMessage = document.getElementById('statusMessage');

    // 1. Manejo del Envío del Formulario
    form.addEventListener('submit', async function(event) {
        // Previene el comportamiento por defecto del formulario (recarga de página)
        event.preventDefault();

        // 1.1 Preparación de la Interfaz de Usuario
        // Deshabilita el botón de envío para prevenir múltiples clicks
        submitButton.disabled = true;
        submitButton.textContent = 'Enviando...';
        statusMessage.textContent = 'Procesando imágenes y buscando en DB...';
        // Limpia las clases de estilo de estado previas (success, error, warning)
        statusMessage.classList.remove('hidden', 'success', 'error', 'warning');

        // Crea un objeto FormData para encapsular todos los campos del formulario, 
        // incluyendo archivos binarios (imágenes)
        const formData = new FormData(form);

        try {
            // 2. Solicitud Fetch a la API de FastAPI
            // Realiza una solicitud POST asíncrona al endpoint del servidor
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                // El objeto FormData se usa como cuerpo (body) de la solicitud.
                // El navegador automáticamente establece el Content-Type adecuado (multipart/form-data).
                body: formData 
            });

            // Parsea el cuerpo de la respuesta del servidor como un objeto JSON
            const data = await response.json();

            // 3. Manejo de la Respuesta del Servidor (FastAPI)
            // response.ok es true para códigos de estado 200-299
            if (response.ok) {
                
                // Evalúa el campo 'status' devuelto por la lógica del servidor (success o warning)
                if (data.status === 'success') {
                    statusMessage.classList.add('success');
                } else if (data.status === 'warning') {
                    statusMessage.classList.add('warning');
                }
                
                // Muestra la placa detectada y el mensaje de procesamiento final al usuario
                statusMessage.textContent = `Placa detectada: ${data.placa_detectada}. Mensaje del servidor: ${data.mensaje}`;
                // Restablece los campos del formulario tras el envío exitoso
                form.reset();
            } else {
                // response.ok es false para códigos de error (4xx o 5xx)
                statusMessage.classList.add('error');
                // Muestra el mensaje de error detallado devuelto por la API
                statusMessage.textContent = `Error del servidor: ${data.detail || data.mensaje || 'Error desconocido'}`;
            }

        } catch (error) {
            // Captura errores que impiden la comunicación HTTP (ej. servidor inactivo, fallo de red)
            console.error('Error de conexión o red:', error);
            statusMessage.classList.add('error');
            statusMessage.textContent = `Error de conexión. Asegúrate de que el servidor (${SERVER_IP}:${SERVER_PORT}) esté corriendo y la IP sea correcta.`;
        } finally {
            // El bloque finally se ejecuta después de try o catch, restableciendo el estado del botón
            submitButton.disabled = false;
            submitButton.textContent = 'Enviar Reporte';
        }
    });

    // 4. Registro del Service Worker para PWA
    // Verifica si el navegador soporta la API de Service Workers
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            // Registra el archivo 'service-worker.js' para habilitar las funcionalidades de PWA
            navigator.serviceWorker.register('service-worker.js')
                .then(reg => console.log('Service Worker registrado:', reg.scope))
                .catch(err => console.log('Fallo el registro del Service Worker:', err));
        });
    }
});