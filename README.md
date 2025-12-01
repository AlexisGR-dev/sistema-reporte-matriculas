# Ejecución del Sistema

## Servidores Necesarios

### Terminal 1 — Backend

* *Rol:* API, OCR, Lógica de BD
* *Comando:*

  bash
  python server/main.py
  
* *Puerto:* *8000*

### Terminal 2 — Frontend

* *Rol:* Servidor Web Estático
* *Comando (desde /frontend/):*

  bash
  python -m http.server 5000
  
* *Puerto:* *5000*

# Uso de la Aplicación (Acceso desde Móvil)

1. *Determinar la IP local:*
   Busca la dirección *IPv4* de tu computadora, por ejemplo:

   
   192.168.100.132
   

2. *Acceder al Frontend desde el móvil:*
   En el navegador del dispositivo, ir a:

   
   http://[TU_IP_LOCAL]:5000/index.html
   

3. *Instalar como PWA:*
   Usa la opción *“Añadir a pantalla de inicio”* del navegador para instalar la app.

# Arquitectura de la Base de Datos (Supabase)

| Objeto                 | Propósito                              | Seguridad                                    |
| ---------------------- | -------------------------------------- | -------------------------------------------- |
| *propietarios*       | Tablas base                            | Escritura protegida con *service_role*     |
| *vehiculos*          | Tablas base                            | Escritura protegida con *service_role*     |
| *reportes*           | Tablas base                            | Escritura protegida con *service_role*     |
| *reporte_datos_view* | Vista que une vehículos y propietarios | Búsqueda rápida para notificaciones          |
| *reportes-evidencia* | Bucket de Storage                      | Almacena imágenes como evidencia de reportes |

Si quieres, puedo generarte una versión lista para imprimir o en estilo guía rápida.
[11:50 p.m., 30/11/2025] Johan Abel Camacho Medina Feliz Cum: Aquí tienes *el mismo texto exactamente como lo diste, sin reducir nada, solo con **formato Markdown llamativo*:

# Ejecución del Sistema

## Requiere la ejecución de dos servidores en terminales separadas:

### Terminal 1 (Backend)

* *Rol:* API, OCR, DB Logic
* *Comando:*

  bash
  python server/main.py
  
* *Puerto:* *8000*

### Terminal 2 (Frontend)

* *Rol:* Servidor Web Estático
* *Comando (desde /frontend/):*

  bash
  python -m http.server 5000
  
* *Puerto:* *5000*

---

# Uso de la Aplicación (Acceso Móvil)

### Determinar la IP

Encuentre la dirección IPv4 local de su PC (ej., *192.168.100.132*).

### Acceder al Frontend

En el navegador de su móvil, navegue a la URL del Frontend:


http://[Tu_IP_Local]:5000/index.html


### Instalar PWA

Utilice la opción *"Añadir a pantalla de inicio"* del navegador para instalar la aplicación en su dispositivo.

---

# Arquitectura de la Base de Datos

El backend interactúa con las siguientes estructuras en Supabase:

## Tablas y Objetos

| Objeto                 | Propósito                               | Seguridad                                  |
| ---------------------- | --------------------------------------- | ------------------------------------------ |
| *propietarios*       | Tablas base.                            | Escritura protegida por service_role       |
| *vehiculos*          | Tablas base.                            | Escritura protegida por service_role       |
| *reportes*           | Tablas base.                            | Escritura protegida por service_role       |
| *reporte_datos_view* | Vista que une vehiculos y propietarios. | Usada para búsqueda rápida de notificación |
| *reportes-evidencia* | Supabase Storage Bucket.                | Almacena las imágenes de prueba            |
