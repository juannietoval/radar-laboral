import os
import sys
import time
import json
import uuid
import subprocess
import threading
from typing import Dict, Any, Optional, List

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(CURRENT_DIR, "cache")
PROFILES_FILE = os.path.join(CURRENT_DIR, "profiles.json")

# In-memory tracking of active agent runs
AGENT_JOBS: Dict[str, Dict[str, Any]] = {}

def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    job = AGENT_JOBS.get(job_id)
    if not job:
        return None
    if job["status"] == "running":
        job["elapsed_seconds"] = round(time.time() - job["start_time"], 1)
    return job

def _load_profile(profile_id: str) -> Dict[str, Any]:
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            profiles = json.load(f)
            for p in profiles:
                if p["id"] == profile_id:
                    return p
    return {"name": "Perfil General", "positive_skills": []}

def _load_cached_jobs(profile_id: str) -> List[Dict[str, Any]]:
    cache_path = os.path.join(CACHE_DIR, f"{profile_id}.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def _run_agy_process(job_id: str, prompt: str):
    job = AGENT_JOBS[job_id]
    job["logs"].append(f"[{time.strftime('%H:%M:%S')}] Conectando con Antigravity CLI (agy.exe)...")
    
    try:
        cmd = ["agy.exe", "-p", prompt, "--effort", "low", "--output-format", "text"]
        
        job["logs"].append(f"[{time.strftime('%H:%M:%S')}] Ejecutando comando en terminal: agy.exe -p ...")
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        job["pid"] = proc.pid

        # Monitor output while running
        stdout, stderr = proc.communicate()
        job["elapsed_seconds"] = round(time.time() - job["start_time"], 1)
        
        if proc.returncode == 0:
            job["status"] = "completed"
            job["response"] = stdout.strip()
            job["logs"].append(f"[{time.strftime('%H:%M:%S')}] Proceso completado exitosamente en {job['elapsed_seconds']}s.")
        else:
            job["status"] = "failed"
            job["error"] = stderr.strip() or f"Código de salida: {proc.returncode}"
            job["logs"].append(f"[{time.strftime('%H:%M:%S')}] Error en ejecucion (codigo {proc.returncode}): {job['error']}")

    except FileNotFoundError:
        job["status"] = "failed"
        job["error"] = "No se encontro el comando agy.exe en el PATH del sistema."
        job["logs"].append(f"[{time.strftime('%H:%M:%S')}] ERROR: agy.exe no disponible.")
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        job["logs"].append(f"[{time.strftime('%H:%M:%S')}] Excepcion inesperada: {str(e)}")

def start_agent_task(
    user_message: str,
    profile_id: str = "temporales_vacaciones_freelance",
    selected_job_data: Optional[Dict[str, Any]] = None
) -> str:
    job_id = f"task_{str(uuid.uuid4())[:8]}"
    start_time = time.time()
    
    profile = _load_profile(profile_id)
    cached_jobs = _load_cached_jobs(profile_id)
    
    # Select top 8 most viable/relevant jobs
    top_candidates = cached_jobs[:8]
    
    jobs_context_lines = []
    for idx, c in enumerate(top_candidates, 1):
        jobs_context_lines.append(
            f"OFERTA #{idx}:\n"
            f"- Titulo: {c.get('title')}\n"
            f"- Empresa: {c.get('company')} | Ubicacion: {c.get('location')}\n"
            f"- Salario: {c.get('salary', {}).get('display', 'No especificado')}\n"
            f"- Modalidad: {c.get('modality')} | Tipo/Jornada: {c.get('jornada')} | Turno: {c.get('turno')}\n"
            f"- Viabilidad de contratacion: {c.get('viability_score')}% ({c.get('viability_level')})\n"
            f"- Nivel de competencia: {c.get('competition_level')} | Publicado: {c.get('date_posted')}\n"
            f"- Requisitos clave: {', '.join(c.get('requirements', []))}\n"
            f"- Enlace directo oficial: {c.get('job_url')}\n"
        )
    
    selected_context = ""
    if selected_job_data:
        selected_context = (
            f"\n[VACANTE ACTUALMENTE SELECCIONADA POR EL USUARIO EN EL INSPECTOR]:\n"
            f"- Titulo: {selected_job_data.get('title')}\n"
            f"- Empresa: {selected_job_data.get('company')} - {selected_job_data.get('location')}\n"
            f"- Salario: {selected_job_data.get('salary', {}).get('display')}\n"
            f"- Modalidad: {selected_job_data.get('modality')}\n"
            f"- Jornada: {selected_job_data.get('jornada')} | Turno: {selected_job_data.get('turno')}\n"
            f"- Requisitos: {', '.join(selected_job_data.get('requirements', []))}\n"
            f"- Enlace: {selected_job_data.get('job_url')}\n"
            f"- Descripcion completa: {selected_job_data.get('description_full', '')[:600]}\n"
        )

    prompt = f"""Actuas como el Agente Inteligente de 'Radar Laboral' ejecutado desde Antigravity CLI.
Tu rol es ser el analista de carrera del usuario, interactuando con los datos reales encontrados en la app.

=== CONTEXTO DE VACANTES REALES EN LA APP ===
Perfil activo: {profile.get('name')}
Total vacantes indexadas en la aplicacion: {len(cached_jobs)}
{selected_context}
OFERTAS MAS RELEVANTES DISPONIBLES EN ESTE MOMENTO:
{''.join(jobs_context_lines)}

=== MENSAJE / CONSULTA DEL USUARIO ===
"{user_message}"

=== INSTRUCCIONES ESTRICTAS ===
1. Responde basandote EXCLUSIVAMENTE en las ofertas reales provistas arriba. NO inventes vacantes, empresas ni salarios.
2. Si el usuario te indica caracteristicas de su perfil (horarios, disponibilidad, si estudia, o nivel de experiencia), evalua con precision cuales de estas vacantes le convienen de verdad y descarta las que tengan barreras (como turnos incompatibles o exigencia de años de experiencia).
3. Si el usuario pide ayuda para postularse a una oferta, redacta un mensaje de contacto / carta de presentacion personalizado para esa empresa, destacando como encaja con los requisitos reales de la oferta.
4. Incluye siempre el enlace oficial provisto para que el usuario pueda aplicar directamente.
5. Formato: Markdown limpio, estructurado y profesional. NO uses emojis ni stickers decorativos."""

    AGENT_JOBS[job_id] = {
        "job_id": job_id,
        "status": "running",
        "start_time": start_time,
        "elapsed_seconds": 0.0,
        "prompt_summary": user_message[:60],
        "logs": [
            f"[{time.strftime('%H:%M:%S')}] Tarea registrada para perfil '{profile.get('name')}'.",
            f"[{time.strftime('%H:%M:%S')}] Inyectando {len(top_candidates)} vacantes reales en contexto..."
        ],
        "response": "",
        "error": ""
    }

    thread = threading.Thread(target=_run_agy_process, args=(job_id, prompt), daemon=True)
    thread.start()

    return job_id
