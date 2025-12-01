// Define el nombre de la caché actual. Al cambiar este nombre (ej. a 'reporte-v3'),
// se fuerza al navegador a descartar la caché anterior y descargar todos los archivos nuevos.
const CACHE_NAME = 'reporte-v2';

// Lista de URLs y rutas de archivos que deben ser almacenados en la caché del Service Worker.
// Esto permite que la aplicación funcione sin conexión (offline).
const urlsToCache = [
    '/', // La raíz del sitio (generalmente la página principal)
    'index.html', // Página del formulario de reporte
    'js/script.js', // Lógica de la API y el formulario
    'css/style.css', // Hojas de estilo
    'js/reportes.js', // Lógica para la vista de reportes
    'manifest.json', // Archivo de configuración de la PWA
    'images/icon-192x192.png', // Icono para dispositivos móviles
    'images/icon-512x512.png' // Icono de alta resolución
];

// Evento 'install': Se dispara la primera vez que el Service Worker es registrado
// y cada vez que el archivo de caché cambia.
self.addEventListener('install', event => {
    console.log('Service Worker: Evento Install');
    // waitUntil asegura que el Service Worker no se considere instalado hasta que la promesa se resuelva
    event.waitUntil(
        // Abre el objeto de caché con el nombre definido
        caches.open(CACHE_NAME)
            .then(cache => {
                // cache.addAll descarga todos los recursos listados en urlsToCache y los guarda
                return cache.addAll(urlsToCache);
            })
    );
});

// Evento 'fetch': Se dispara cada vez que el navegador hace una solicitud de red
// (por ejemplo, al cargar un recurso o una imagen).
self.addEventListener('fetch', event => {
    // intercepta la solicitud de red y define cómo responder
    event.respondWith(
        // Intenta encontrar la solicitud entrante (event.request) dentro de las cachés disponibles
        caches.match(event.request)
            .then(response => {
                // Estrategia Cache-First (Primero la Caché):
                // Si 'response' existe (el archivo está cacheado), lo devuelve inmediatamente.
                // Si no existe, realiza una solicitud de red normal (fetch(event.request)).
                return response || fetch(event.request);
            })
    );
});