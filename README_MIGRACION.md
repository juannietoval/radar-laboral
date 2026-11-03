# Guía de Migración a Otro Dispositivo — Radar Laboral Minimalista

Esta aplicación fue diseñada para ser **100% portable y ligera**. No requiere bases de datos externas, servidores pagos, ni herramientas complejas de Node.js/npm. Todo el frontend corre con JavaScript nativo y Tailwind vía CDN, y el backend utiliza FastAPI y Python puro.

---

## 1. Requisito Único en el Nuevo Equipo
- Tener instalado **Python 3.10 o superior** (descargable desde [python.org](https://www.python.org/downloads/)).
- **Punto crítico en Windows:** Durante la instalación de Python, asegurarse de marcar la casilla **"Add python.exe to PATH"**.

---

## 2. Método Rápido (USB, Carpeta Compartida o Archivo ZIP)

### Paso 1: Qué carpetas copiar
Copia únicamente la carpeta `app_empleo` a tu USB o compáctala en un archivo ZIP:
```text
app_empleo/
├── cache/                  (Opcional: contiene las vacantes ya indexadas)
├── static/
│   └── index.html          (Interfaz web minimalista)
├── computrabajo_scraper.py
├── iniciar_radar.bat       (Lanzador automático 1-clic para Windows)
├── iniciar_radar.sh        (Lanzador automático para Linux/Mac)
├── parser.py
├── profiles.json           (Tus 4 perfiles y criterios)
├── requirements.txt        (Librerías necesarias)
├── run_app.bat
├── scraper.py
└── server.py
```

> **REGLA FUNDAMENTAL:** **NUNCA copies la carpeta `.venv`**. Los entornos virtuales contienen rutas fijas del disco de tu equipo anterior y binarios compilados específicos. Deja que el nuevo equipo cree su propio `.venv` limpio.

### Paso 2: Iniciar en el nuevo equipo
En el nuevo computador, simplemente haz **doble clic en `iniciar_radar.bat`**:
1. El script detectará que es la primera vez que se ejecuta en esa máquina.
2. Creará automáticamente el entorno virtual `.venv`.
3. Descargará e instalará las librerías desde `requirements.txt` en ~30 segundos.
4. Abrirá tu navegador predeterminado en `http://localhost:8080`.

---

## 3. Método por Git / GitHub (Si usas repositorio)

1. En el nuevo equipo, clona el repositorio:
   ```bash
   git clone <URL_DE_TU_REPOSITORIO>
   cd app_empleo
   ```
2. Ejecuta:
   - En Windows: doble clic en `iniciar_radar.bat`.
   - En Linux / macOS: `bash iniciar_radar.sh`.
