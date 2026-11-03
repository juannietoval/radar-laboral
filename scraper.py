import json
import os
import sys
import time
from typing import List, Dict, Any, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import pandas as pd
from jobspy import scrape_jobs
from parser import process_job_row
from computrabajo_scraper import scrape_computrabajo

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
PROFILES_FILE = os.path.join(os.path.dirname(__file__), "profiles.json")

os.makedirs(CACHE_DIR, exist_ok=True)

def load_profiles() -> List[Dict[str, Any]]:
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def get_profile_by_id(profile_id: str) -> Optional[Dict[str, Any]]:
    profiles = load_profiles()
    for p in profiles:
        if p["id"] == profile_id:
            return p
    return None

def fetch_jobs_for_profile(
    profile_id: str,
    custom_query: Optional[str] = None,
    sites: Optional[List[str]] = None,
    location: str = "Risaralda, Colombia",
    results_wanted: int = 30,
    force_refresh: bool = False
) -> List[Dict[str, Any]]:
    profile = get_profile_by_id(profile_id)
    if not profile:
        profile = {
            "id": "custom",
            "name": "Búsqueda personalizada",
            "search_queries": [custom_query] if custom_query else ["vacaciones pereira", "asesor virtual"],
            "positive_skills": ["vacaciones", "temporada", "asesor", "asistente", "remoto", "pereira", "sin experiencia"],
            "negative_keywords": ["gerente", "director"]
        }

    sites_to_use = sites or ["linkedin", "indeed"]
    queries_to_run = [custom_query] if custom_query else profile.get("search_queries", ["empleo"])

    cache_key = f"{profile['id']}.json"
    cache_path = os.path.join(CACHE_DIR, cache_key)

    if not force_refresh and os.path.exists(cache_path):
        mtime = os.path.getmtime(cache_path)
        if (time.time() - mtime) < 3600:  # 1 hour cache
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    if cached_data and len(cached_data) > 0:
                        return cached_data
            except Exception:
                pass

    all_raw_jobs: List[Dict[str, Any]] = []
    seen_signatures = set()

    for q in queries_to_run[:7]:
        q_lower = q.lower()
        is_remote_query = any(w in q_lower for w in ["remoto", "virtual", "redes", "community", "digitador", "freelance", "asesor virtual"])
        is_local_query = any(w in q_lower for w in ["pereira", "risaralda", "electrico", "mantenimiento", "calidad", "metrologia", "temporada", "vacaciones", "promotor"])

        try:
            if is_remote_query:
                comp_jobs_rem = scrape_computrabajo(query=q, location="remoto", max_pages=2, max_results=20)
                for j in comp_jobs_rem:
                    sig = f"{j['title'].lower()[:25]}_{j['company'].lower()[:20]}"
                    if sig not in seen_signatures:
                        seen_signatures.add(sig)
                        all_raw_jobs.append(j)

            if is_local_query or not is_remote_query:
                comp_jobs_loc = scrape_computrabajo(query=q, location="risaralda", max_pages=2, max_results=20)
                for j in comp_jobs_loc:
                    sig = f"{j['title'].lower()[:25]}_{j['company'].lower()[:20]}"
                    if sig not in seen_signatures:
                        seen_signatures.add(sig)
                        all_raw_jobs.append(j)

        except Exception as e:
            print(f"Error fetching Computrabajo for {q}: {e}")

    primary_query = queries_to_run[0]
    secondary_query = queries_to_run[1] if len(queries_to_run) > 1 else primary_query

    for q_spy in [primary_query, secondary_query]:
        try:
            df: pd.DataFrame = scrape_jobs(
                site_name=sites_to_use,
                search_term=q_spy,
                location="Risaralda, Colombia" if ("pereira" in q_spy or "risaralda" in q_spy) else "Colombia",
                results_wanted=results_wanted,
                country_indeed="Colombia",
                hours_old=168
            )
            if df is not None and not df.empty:
                df = df.where(pd.notnull(df), None)
                for r in df.to_dict("records"):
                    title = str(r.get("title") or "")
                    comp = str(r.get("company") or "")
                    sig = f"{title.lower()[:25]}_{comp.lower()[:20]}"
                    if sig not in seen_signatures:
                        seen_signatures.add(sig)
                        all_raw_jobs.append(r)
        except Exception as e:
            print(f"Error scraping with JobSpy ({q_spy}): {e}")

    processed_jobs: List[Dict[str, Any]] = []
    for raw in all_raw_jobs:
        try:
            item = process_job_row(raw, profile)
            if item["is_match"]:
                processed_jobs.append(item)
        except Exception as ex:
            pass

    processed_jobs.sort(key=lambda x: (x["viability_score"], x["competition_score"], x["match_score"]), reverse=True)

    if processed_jobs:
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(processed_jobs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error caching: {e}")

    return processed_jobs
