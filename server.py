import os
import sys
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scraper import load_profiles, get_profile_by_id, fetch_jobs_for_profile
from agent_service import start_agent_task, get_job_status

app = FastAPI(title="Radar Laboral Minimalista", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

class ProfileCreate(BaseModel):
    id: str
    name: str
    description: str
    search_queries: List[str]
    locations: List[str]
    positive_skills: List[str]
    negative_keywords: List[str]

class AgentChatRequest(BaseModel):
    message: str
    profile_id: str = "temporales_vacaciones_freelance"
    selected_job: Optional[Dict[str, Any]] = None

@app.get("/api/profiles")
def list_profiles():
    return load_profiles()

@app.post("/api/profiles")
def save_profile(profile: ProfileCreate):
    profiles_path = os.path.join(os.path.dirname(__file__), "profiles.json")
    profiles = load_profiles()
    updated = False
    for i, p in enumerate(profiles):
        if p["id"] == profile.id:
            profiles[i] = profile.dict()
            updated = True
            break
    if not updated:
        profiles.append(profile.dict())
    
    with open(profiles_path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)
    return {"status": "ok", "profile": profile.dict()}

@app.get("/api/jobs")
def get_jobs(
    profile_id: str = "temporales_vacaciones_freelance",
    q: Optional[str] = None,
    location: str = "Risaralda, Colombia",
    modality: Optional[str] = None,
    jornada: Optional[str] = None,
    turno: Optional[str] = None,
    min_salary: Optional[float] = None,
    site: Optional[str] = None,
    refresh: bool = False
):
    jobs = fetch_jobs_for_profile(
        profile_id=profile_id,
        custom_query=q,
        location=location,
        results_wanted=30,
        force_refresh=refresh
    )

    filtered = []
    for j in jobs:
        if modality and modality != "Todos" and j["modality"].lower() != modality.lower():
            continue
        if jornada and jornada != "Todos" and j["jornada"].lower() != jornada.lower():
            continue
        if turno and turno != "Todos" and j["turno"].lower() != turno.lower():
            continue
        if site and site != "Todos" and j["site"].lower() != site.lower():
            continue
        if min_salary and min_salary > 0:
            sal = j.get("salary", {})
            if sal.get("min_val", 0) < min_salary and sal.get("max_val", 0) < min_salary:
                continue
        filtered.append(j)

    return {
        "total": len(filtered),
        "profile": get_profile_by_id(profile_id),
        "jobs": filtered
    }

# Agent Antigravity CLI Endpoints
@app.post("/api/agent/chat")
def run_agent_chat(req: AgentChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")
    job_id = start_agent_task(
        user_message=req.message,
        profile_id=req.profile_id,
        selected_job_data=req.selected_job
    )
    return {"status": "ok", "job_id": job_id}

@app.get("/api/agent/status")
def agent_status(job_id: str):
    status_data = get_job_status(job_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="Tarea del agente no encontrada.")
    return status_data

# Mount static files at root
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    import socket

    port = 8080
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('127.0.0.1', 8080))
        s.close()
    except OSError:
        port = 8000

    print(f"Servidor listo en http://localhost:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, reload=False)
