# Sistema de Préstamo de Cubículos y Componentes Electrónicos

Este es un sistema web completo (Backend + Frontend) para la gestión de préstamos de cubículos de estudio y componentes electrónicos dentro de una institución educativa. El sistema permite a los alumnos solicitar espacios y materiales, a los administradores gestionar las solicitudes, y a los encargados de los centros de acopio controlar el inventario.

## Características Principales

*   **Autenticación por Roles:** Login seguro para Alumnos, Docentes, Administradores y Encargados de acopio.
*   **Gestión de Cubículos:** Mapa interactivo para que los alumnos soliciten cubículos disponibles. Los administradores autorizan o rechazan las solicitudes y registran entradas/salidas.
*   **Gestión de Componentes:** Catálogo de componentes electrónicos. Los alumnos solicitan, el administrador autoriza y el encargado del centro de acopio entrega y recibe las devoluciones.
*   **Historial:** Vista detallada de todas las solicitudes y préstamos para alumnos y administradores.
*   **Panel de Control:** Dashboard con estadísticas en tiempo real (solicitudes pendientes, cubículos en uso, etc.).
*   **Manejo de Inventario:** Control estricto de piezas prestadas, devueltas y dañadas/faltantes.

## Tecnologías Utilizadas

*   **Backend:** Python 3 + Flask
*   **Base de Datos:** Microsoft SQL Server (conectado mediante `pyodbc`)
*   **Frontend:** HTML5, CSS3, Vanilla JavaScript (sin frameworks externos)
*   **Seguridad:** Hash de contraseñas con `werkzeug.security`

## 📂 Estructura del Proyecto

```text
/
├── app.py                 # Servidor Flask y lógica del Backend (API REST)
├── schema.sql             # Script de base de datos (SQL Server)
├── requirements.txt       # Dependencias de Python
├── README.md              # Este archivo
└── static/                # Carpeta del Frontend
    ├── index.html         # Interfaz principal
    ├── app.js             # Lógica del cliente (JS)
    └── style.css          # Estilos visuales (CSS)