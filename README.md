# Radar Laboral Minimalista

Plataforma web local, autónoma y de alto rendimiento diseñada para la búsqueda profunda, síntesis ejecutiva y priorización algorítmica de vacantes laborales en **Risaralda / Pereira** y modalidades **100% remotas (Teletrabajo)** en Colombia.

La aplicación elimina la necesidad de leer párrafos extensos e irrelevantes en múltiples portales de empleo, consolidando en una interfaz limpia estilo split-pane (60% listado / 40% inspector ejecutivo) los requisitos clave, salarios reales estructurados, turnos y enlaces directos de postulación oficial.

---

## Principios y Filosofía de Diseño

1. **Cero Datos Simulados (*100% Real-World Data*):** No utiliza datos sintéticos ni enlaces genéricos a páginas de inicio. Cada vacante cuenta con un enlace canónico verificado que redirige directamente a la oferta de trabajo para aplicar de inmediato.
2. **Costo de Operación $0.00 USD:** Funciona exclusivamente con infraestructura y extractores locales (`Computrabajo`, `JobSpy` sobre `Indeed` y `LinkedIn`), sin requerir suscripciones a proxies ni créditos de pago en la nube.
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
│   └── index.html               # Interfaz split-pane reactiva (HTML5, Tailwind CDN, JS Vanilla)
├── cache/                       # Almacenamiento local temporal en JSON para respuesta instantánea
├── server.py                    # API REST local implementada en FastAPI y Uvicorn
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

---

## Licencia

Distribuido bajo la licencia MIT. Libre para uso personal, académico o comercial.
