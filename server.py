import os
import sys
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scraper import load_profiles, get_profile_by_id, fetch_jobs_for_profile

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
    print(f"DEBUG: fetch_jobs_for_profile returned {len(jobs)} items")

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

    print(f"Servidor iniciado en http://localhost:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, reload=False)
