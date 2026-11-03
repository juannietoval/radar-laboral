# Radar Laboral Minimalista

Plataforma web local, autónoma y de alto rendimiento diseñada para la búsqueda profunda, síntesis ejecutiva y priorización algorítmica de vacantes laborales en **Risaralda / Pereira** y modalidades **100% remotas (Teletrabajo)** en Colombia.

La aplicación elimina la necesidad de leer párrafos extensos e irrelevantes en múltiples portales de empleo, consolidando en una interfaz limpia estilo split-pane (60% listado / 40% inspector ejecutivo) los requisitos clave, salarios reales estructurados, turnos y enlaces directos de postulación oficial.

---

## Principios y Filosofía de Diseño

1. **Cero Datos Simulados (*100% Real-World Data*):** No utiliza datos sintéticos ni enlaces genéricos a páginas de inicio. Cada vacante cuenta con un enlace canónico verificado que redirige directamente a la oferta de trabajo para aplicar de inmediato.
2. **Costo de Operación \$0.00 USD:** Funciona exclusivamente con infraestructura y extractores locales (`Computrabajo`, `JobSpy` sobre `Indeed` y `LinkedIn`), sin requerir suscripciones a proxies ni créditos de pago en la nube.
3. **Priorización por Viabilidad Real (*Opportunity First*):** En lugar de ordenar únicamente por coincidencia de palabras clave, evalúa la factibilidad de contratación para perfiles en formación, estudiantes y cargos de entrada, penalizando roles directivos o exigencias desmedidas de experiencia.
4. **Detector de Baja Competencia / Ventana Temprana:** Identifica aquellas ofertas publicadas en las últimas 24 a 48 horas (*golden window*) o con convocatorias masivas urgentes, maximizando la probabilidad de que la hoja de vida sea revisada en la primera fase.
5. **Estética Minimalista y Profesional:** Interfaz sobria, en tonos claros, construida con Tailwind CSS y tipografía moderna, utilizando elementos vectoriales SVG semánticos y sin elementos decorativos distractores.

---

## Perfiles Preconfigurados

El sistema incluye 4 perfiles técnicos y laborales optimizados en `profiles.json`:

| Perfil | Ubicación | Enfoque de Búsqueda |
| :--- | :--- | :--- |
| **Temporales, Vacaciones & Asesor Virtual / Freelance** | Pereira y Remoto | Vacantes inmediatas por temporada navideña/comercial, cubrimiento de vacaciones, asesoría virtual de atención al cliente y tareas freelance con baja competencia. |
| **Estudiante Ing. Eléctrica** | Risaralda y Remoto | Oportunidades para estudiantes de primeros semestres: auxiliares eléctricos y de mantenimiento, dibujante AutoCAD, pasantías y soporte técnico. |
| **Asistente Virtual / Redes / Secretaria** | Remoto y Pereira | Gestión de redes sociales (Instagram, TikTok, WhatsApp), community manager junior, digitación en hojas de cálculo, secretaria virtual y soporte administrativo. |
| **Ingeniero Físico** | Risaralda, Remoto y Nacional | Metrología, control de calidad, instrumentación electrónica, sensores, análisis de datos con Python/Excel y puestos bilingües. |

---

## Arquitectura del Proyecto

```text
radar-laboral/
├── static/
│   └── index.html               # Interfaz split-pane reactiva con cajón de Agente CLI y visor de logs
├── cache/                       # Almacenamiento local temporal en JSON para respuesta instantánea
├── server.py                    # API REST local implementada en FastAPI y Uvicorn
├── agent_service.py             # Servicio del Agente Antigravity CLI (subprocesos agy.exe, logs y temporizador)
├── scraper.py                   # Orquestador concurrente de búsquedas y gestión de caché
├── computrabajo_scraper.py      # Extractor multi-página con enriquecimiento en paralelo (JSON-LD + DOM)
├── parser.py                    # Motor de normalización salarial, turnos, viabilidad y competencia
├── profiles.json                # Configuración de perfiles, palabras clave y filtros de exclusión
├── requirements.txt             # Dependencias del ecosistema Python
├── iniciar_radar.bat            # Lanzador automático inteligente en 1-clic para Windows
├── iniciar_radar.sh             # Lanzador para Linux y macOS
├── .gitignore                   # Exclusión de entornos virtuales y archivos temporales
└── README.md                    # Documentación técnica completa
```

---

## Requisitos Previos

- **Python 3.10 o superior** ([Descargar de python.org](https://www.python.org/downloads/)).
- En Windows: Asegurarse de marcar la opción **"Add python.exe to PATH"** durante la instalación.

---

## Instalación e Inicio Rápido

### En Windows (1-Clic Automático)
Basta con hacer doble clic en el archivo:
```text
iniciar_radar.bat
```
El script detectará automáticamente si el entorno virtual `.venv` existe. De no ser así, lo creará, instalará las dependencias de `requirements.txt` y abrirá la aplicación en tu navegador predeterminado en `http://localhost:8080`.

### En Linux / macOS
```bash
chmod +x iniciar_radar.sh
./iniciar_radar.sh
```

### Ejecución Manual desde la Terminal
```bash
# 1. Crear el entorno virtual
python -m venv .venv

# 2. Activar el entorno virtual
# En Windows:
.venv\Scripts\activate
# En Linux/macOS:
source .venv/bin/activate

# 3. Instalar librerías requeridas
pip install -r requirements.txt

# 4. Iniciar el servidor
python server.py
```
Acceder en el navegador a: [http://localhost:8080](http://localhost:8080)

---

## Capacidades del Algoritmo de Análisis

### 1. Extracción y Normalización de Compensación
Analiza etiquetas estructuradas `schema.org/JobPosting` y patrones regex en texto para extraer montos en COP, USD o SMLV, distinguiendo rangos salariales reales (por ejemplo, `$1.900.000 - $2.200.000 COP`) y catalogando aquellas ofertas donde la remuneración es a convenir.

### 2. Detección de Turno y Jornada
Clasifica de manera automática la modalidad de trabajo:
- **Jornada:** Tiempo Completo, Medio Tiempo, Pasantía / Prácticas, Licencia / Temporal Vacaciones, Freelance / Por Tareas.
- **Turno:** Diurno / Oficina (Lunes a Viernes), Turnos Rotativos (Diurno / Nocturno), Nocturno, Horario Flexible.

### 3. Índice de Viabilidad de Contratación
Puntaje de 0 a 100 que pondera la accesibilidad del cargo:
- **Bonificadores:** Sin experiencia previa requerida (+28 pts), perfil para estudiantes o aprendices (+22 pts), puesto temporal/vacacional (+20 pts), capacitación paga e ingreso inmediato (+14 pts).
- **Penalizadores:** Exigencia de cargos directivos o gerenciales (-35 pts), más de 3 a 5 años de experiencia (-18 a -30 pts), posgrados o especializaciones (-20 pts).

### 4. Nivel de Postulaciones y Concurrencia
Calcula una estimación de competencia para priorizar las postulaciones tempranas:
- **Pocas Postulaciones (< 24h - 48h):** Ofertas recién publicadas donde el aspirante forma parte de los primeros evaluados.
- **Múltiples Vacantes / Urgente:** Convocatorias masivas donde la tasa de selección por cupo es más favorable.

### 5. Asistente y Analista con Antigravity CLI
La aplicación integra un panel lateral interactivo impulsado por el motor local de **Antigravity CLI** (`agy.exe`) sin costos de API externa ni dependencias de nube:
- **Lectura de Datos Reales:** El agente recibe el perfil activo, los requisitos declarados y el conjunto de vacantes recién indexadas.
- **Evaluación de Compatibilidad:** Al pulsar "Consultar Agente con esta Vacante", analiza los requisitos detallados, turnos rotativos y salarios contrastándolos con la disponibilidad del usuario.
- **Generación de Cartas de Postulación:** Redacta mensajes de presentación técnicos y profesionales listos para enviar a la empresa.
- **Monitoreo en Tiempo Real:** Dispone de un cronómetro de ejecución activa en segundos, indicador de estado (`running`, `completed`, `failed`) y una consola expandible con el flujo de eventos de terminal en vivo.

---

## Licencia

Distribuido bajo la licencia MIT. Libre para uso personal, académico o comercial.
