import re
import math
from typing import Dict, Any, List, Optional

def clean_text(text: Any) -> str:
    if text is None:
        return ""
    if isinstance(text, float) and (math.isnan(text) or math.isinf(text)):
        return ""
    text_str = str(text)
    if text_str.lower() == "nan":
        return ""
    return re.sub(r'\s+', ' ', text_str).strip()

def extract_salary_info(row: Dict[str, Any]) -> Dict[str, Any]:
    min_amt = row.get("min_amount")
    max_amt = row.get("max_amount")
    currency = clean_text(row.get("currency")) or "COP"
    interval = clean_text(row.get("interval")) or "monthly"
    
    # 1. Check if structured salary exists
    if min_amt is not None and not (isinstance(min_amt, float) and math.isnan(min_amt)) and str(min_amt) != "nan":
        try:
            min_val = float(min_amt)
            max_val = float(max_amt) if max_amt is not None and str(max_amt) != "nan" and not (isinstance(max_amt, float) and math.isnan(max_amt)) else min_val
            if min_val > 0:
                if currency.upper() == "COP" or min_val > 100000:
                    formatted = f"${min_val:,.0f} - ${max_val:,.0f} COP" if max_val > min_val else f"${min_val:,.0f} COP"
                else:
                    formatted = f"${min_val:,.0f} - ${max_val:,.0f} {currency}" if max_val > min_val else f"${min_val:,.0f} {currency}"
                return {
                    "has_salary": True,
                    "min_val": min_val,
                    "max_val": max_val,
                    "currency": currency,
                    "interval": interval,
                    "display": formatted.replace(",", ".")
                }
        except (ValueError, TypeError):
            pass
    
    # 2. Heuristic extraction from description
    desc = clean_text(row.get("description"))
    
    # Match COP formats: $1.500.000, 2'500.000, etc.
    cop_pattern = r'(\$?\s?([1-9]\d{0,2}(?:[\.,\']\d{3}){2})\b(?:\s*(?:a|-|hasta)\s*\$?\s?([1-9]\d{0,2}(?:[\.,\']\d{3}){2}))?)'
    match = re.search(cop_pattern, desc)
    if match:
        raw_min = match.group(2).replace(".", "").replace(",", "").replace("'", "")
        try:
            val_min = float(raw_min)
            if 800000 <= val_min <= 50000000:
                raw_max = match.group(3).replace(".", "").replace(",", "").replace("'", "") if match.group(3) else None
                val_max = float(raw_max) if raw_max else val_min
                display_str = f"${val_min:,.0f} - ${val_max:,.0f} COP" if val_max > val_min else f"${val_min:,.0f} COP"
                return {
                    "has_salary": True,
                    "min_val": val_min,
                    "max_val": val_max,
                    "currency": "COP",
                    "interval": "monthly",
                    "display": display_str.replace(",", ".")
                }
        except ValueError:
            pass

    # Match SMLV
    if re.search(r'\b(smlv|salario m[ií]nimo)\b', desc, re.IGNORECASE):
        return {
            "has_salary": True,
            "min_val": 1423500,
            "max_val": 1423500,
            "currency": "COP",
            "interval": "monthly",
            "display": "Salario Mínimo Legal (SMLV)"
        }

    # Match USD hourly or monthly for remote jobs
    usd_match = re.search(r'\$(\d{2,4})\s?(?:usd|d[oó]lares)?\s?(?:al mes|\/mes|\/month|monthly)', desc, re.IGNORECASE)
    if usd_match:
        val = float(usd_match.group(1))
        return {
            "has_salary": True,
            "min_val": val,
            "max_val": val,
            "currency": "USD",
            "interval": "monthly",
            "display": f"${val:,.0f} USD/mes"
        }

    return {
        "has_salary": False,
        "min_val": 0,
        "max_val": 0,
        "currency": "COP",
        "interval": "monthly",
        "display": "A convenir / No especificado"
    }

def detect_modality(title: str, desc: str, location: str, is_remote: Any) -> str:
    text = f"{title} {desc} {location}".lower()
    if is_remote is True or "100% remoto" in text or "teletrabajo" in text or "work from home" in text or "desde casa" in text or "home office" in text or "remoto" in text:
        if "híbrido" in text or "hibrido" in text or "semi-presencial" in text:
            return "Híbrido"
        return "Remoto"
    if "híbrido" in text or "hibrido" in text or "hybrid" in text:
        return "Híbrido"
    return "Presencial"

def detect_schedule(job_type: Optional[str], desc: str) -> Dict[str, str]:
    text = f"{job_type or ''} {desc}".lower()
    
    # Jornada
    jornada = "Tiempo Completo"
    if "freelance" in text or "por tareas" in text or "honorarios" in text:
        jornada = "Freelance / Por Tareas"
    elif "medio tiempo" in text or "part-time" in text or "media jornada" in text or "por horas" in text:
        jornada = "Medio Tiempo"
    elif "pasantía" in text or "pasantia" in text or "prácticas" in text or "practicas" in text or "aprendiz" in text or "internship" in text:
        jornada = "Pasantía / Prácticas"
    elif "vacaciones" in text:
        jornada = "Licencia / Temporal Vacaciones"
    elif "temporada" in text or "navideñ" in text:
        jornada = "Temporal de Temporada"
    elif "obra o labor" in text:
        jornada = "Tiempo Completo (Obra o Labor)"
    elif "temporal" in text or "por proyecto" in text:
        jornada = "Temporal / Por Proyecto"
        
    # Turno
    turno = "Diurno / Oficina (Lunes a Viernes)"
    if any(k in text for k in ["rotativo", "turnos rotativos", "diurnos y nocturnos", "domingo a domingo", "24/7"]):
        turno = "Turnos Rotativos (Diurno / Nocturno)"
    elif "nocturno" in text or "noche" in text:
        turno = "Nocturno"
    elif "flexible" in text or "horario flexible" in text:
        turno = "Horario Flexible"

    return {
        "jornada": jornada,
        "turno": turno
    }

def estimate_competition(date_posted: str, desc: str, title: str) -> Dict[str, Any]:
    """
    Estimates competition and application density.
    Identifies postings in early application windows (golden window < 48 hours),
    multiple vacancies, and urgent hiring requests where applicant pressure is lowest.
    """
    text = f"{title} {desc} {date_posted}".lower()
    date_lower = date_posted.lower()

    score = 50
    reasons = []

    # 1. Freshness analysis (Fewer applicants applied so far)
    if any(w in date_lower for w in ["hora", "horas", "hoy"]):
        score = 90
        reasons.append("Publicación muy reciente (< 24h): sé de los primeros en postularte")
    elif any(w in date_lower for w in ["ayer", "1 día", "2 días"]):
        score = 75
        reasons.append("Publicación temprana (1-2 días): proceso de recepción inicial activo")
    elif any(w in date_lower for w in ["3 días", "4 días", "5 días"]):
        score = 55
        reasons.append("Convocatoria abierta estándar")
    elif any(w in date_lower for w in ["semana", "días", "mes"]):
        score = 30
        reasons.append("Oferta con varios días activa (mayor acumulación de candidatos)")

    # 2. Boost for multiple vacancies or mass hiring
    if any(k in text for k in ["múltiples vacantes", "vacantes", "convocatoria masiva", "temporada", "urgente"]):
        score = min(98, score + 12)
        if "urgente" in text or "inmediat" in text:
            reasons.append("Contratación urgente / Inmediata (alta receptividad)")
        else:
            reasons.append("Múltiples cupos disponibles para esta vacante")

    if score >= 75:
        level = "Pocas Postulaciones"
        badge = "Baja Competencia (Fácil Ingreso)"
    elif score >= 50:
        level = "Competencia Moderada"
        badge = "Competencia Moderada"
    else:
        level = "Alta Concurrencia"
        badge = "Muchas Postulaciones"

    return {
        "score": score,
        "level": level,
        "badge": badge,
        "reason": reasons[0] if reasons else "Convocatoria con flujo regular de aspirantes."
    }

def extract_key_requirements(desc: str, raw_bullets: Optional[List[str]] = None) -> List[str]:
    reqs = []
    text_lower = desc.lower()

    if raw_bullets:
        for b in raw_bullets:
            b_clean = b.strip()
            if any(term in b_clean.lower() for term in ["experiencia", "educación", "carrera", "técnico", "profesional"]):
                reqs.append(b_clean)

    # 1. Exact experience requirement
    exp_match = re.search(r'experiencia\s*(?:m[ií]nima)?\s*(?:de\s*)?(\d+)\s*(a[ñn]os?|meses?)', text_lower)
    if exp_match:
        qty = exp_match.group(1)
        unit = "año" if "año" in exp_match.group(2) else "mes"
        if int(qty) > 1 and unit == "año":
            unit = "años"
        elif int(qty) > 1:
            unit = "meses"
        req_exp = f"Experiencia mínima requerida: {qty} {unit}."
        if req_exp not in reqs:
            reqs.append(req_exp)
    elif any(k in text_lower for k in ["sin experiencia", "no requiere experiencia", "primer empleo"]):
        reqs.append("No requiere experiencia previa (Perfil de entrada).")

    # 2. Industry technical certifications & skills
    if "alturas" in text_lower and not any("alturas" in r.lower() for r in reqs):
        reqs.append("Certificación vigente de trabajo en alturas.")
    if ("conte" in text_lower or "tarjeta profesional" in text_lower) and not any("conte" in r.lower() for r in reqs):
        reqs.append("Tarjeta profesional / Matrícula CONTE.")
    if "retie" in text_lower and not any("retie" in r.lower() for r in reqs):
        reqs.append("Conocimiento de normativa RETIE.")
    if "autocad" in text_lower and not any("autocad" in r.lower() for r in reqs):
        reqs.append("Manejo de AutoCAD para planos y diagramas.")
    if ("redes sociales" in text_lower or "community manager" in text_lower or "instagram" in text_lower) and not any("redes" in r.lower() for r in reqs):
        reqs.append("Gestión de redes sociales y contenido digital.")
    if ("asesor" in text_lower or "servicio al cliente" in text_lower or "atención al cliente" in text_lower or "chat" in text_lower) and not any("cliente" in r.lower() for r in reqs):
        reqs.append("Atención y servicio al cliente (mensajería o llamadas).")
    if "excel" in text_lower and not any("excel" in r.lower() for r in reqs):
        reqs.append("Manejo de Excel (fórmulas, tablas, reportes).")
    if ("ingl" in text_lower or "english" in text_lower or "biling" in text_lower) and not any("ingl" in r.lower() for r in reqs):
        reqs.append("Inglés conversacional o técnico.")
    if ("rotativo" in text_lower or "domingo a domingo" in text_lower) and not any("rotativo" in r.lower() for r in reqs):
        reqs.append("Disponibilidad para turnos rotativos.")
    if ("viajar" in text_lower or "viajes" in text_lower) and not any("viajar" in r.lower() for r in reqs):
        reqs.append("Disponibilidad para desplazamientos o viajes.")
    if ("moto" in text_lower or "veh[ií]culo" in text_lower or "licencia" in text_lower) and not any("licencia" in r.lower() for r in reqs):
        reqs.append("Licencia de conducción o vehículo propio.")

    if not reqs:
        if "vacaciones" in text_lower or "temporada" in text_lower or "temporal" in text_lower:
            reqs.append("Vinculación de temporada o temporal con disponibilidad inmediata.")
        elif "estudiante" in text_lower or "aprendiz" in text_lower:
            reqs.append("Perfil formativo orientado a estudiantes o aprendices.")
        elif "profesional" in text_lower or "ingenier" in text_lower:
            reqs.append("Formación universitaria en ingeniería o carrera afín.")
        else:
            reqs.append("Conocimientos prácticos acordes a las funciones del cargo.")

    return reqs[:4]

def calculate_viability(title: str, desc: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    text = f"{title} {desc}".lower()
    title_lower = title.lower()

    viability = 50
    reasons = []

    # 1. High viability boosters (Entry level / Student / Junior / Temporary)
    if any(k in text for k in ["sin experiencia", "no requiere experiencia", "primer empleo", "0 a 6 meses"]):
        viability += 28
        reasons.append("No exige experiencia previa (rápida contratación)")

    if any(k in text for k in ["vacaciones", "temporada", "temporal", "freelance"]):
        viability += 20
        reasons.append("Puesto temporal/vacacional de vinculación inmediata")

    if any(k in text for k in ["estudiante", "aprendiz", "sena", "pasantía", "pasantia", "practicante"]):
        viability += 22
        reasons.append("Orientado a estudiantes o aprendices")

    if any(k in title_lower for k in ["auxiliar", "asistente", "junior", "apoyo", "operativo", "asesor"]):
        viability += 16
        reasons.append("Rol inicial o asesor con baja barrera de ingreso")

    if any(k in text for k in ["capacitación paga", "capacitacion paga", "ingreso inmediato", "vinculación directa", "urgente"]):
        viability += 14
        reasons.append("Capacitación paga / Ingreso inmediato")

    if any(k in text for k in ["medio tiempo", "part-time", "horario flexible", "vacaciones"]):
        viability += 10
        reasons.append("Horario flexible o vacacional compatible con estudio")

    # Location boost for Pereira / Risaralda or Remote
    if any(city in text for city in ["pereira", "dosquebradas", "risaralda"]):
        viability += 8
        reasons.append("Ubicación local en Risaralda / Pereira")
    elif any(r in text for r in ["remoto", "teletrabajo", "desde casa"]):
        viability += 8
        reasons.append("Modalidad 100% remota / desde casa")

    # 2. Viability barriers (Downrank high-experience / leadership)
    if any(lead in title_lower for lead in ["gerente", "director", "jefe", "líder nacional", "coordinador general"]):
        viability -= 35
        reasons.append("Rol directivo/gerencial (baja viabilidad para perfil inicial)")

    exp_match = re.search(r'experiencia\s*(?:m[ií]nima)?\s*(?:de\s*)?(\d+)\s*(a[ñn]os?)', text)
    if exp_match:
        years = int(exp_match.group(1))
        if years >= 5:
            viability -= 30
            reasons.append(f"Exige {years} años de experiencia profesional")
        elif years >= 3:
            viability -= 18
            reasons.append(f"Exige {years} años de experiencia")
        elif years >= 2:
            viability -= 8

    if any(k in text for k in ["posgrado", "maestría", "maestria", "especialización"]):
        viability -= 20
        reasons.append("Exige estudios de posgrado o especialización")

    final_viability = min(98, max(15, viability))

    if final_viability >= 75:
        level = "Alta Viabilidad"
        summary = "Excelente oportunidad de ingreso inmediato o perfil formativo sin barreras complejas."
    elif final_viability >= 50:
        level = "Viabilidad Media"
        summary = "Oportunidad accesible con requisitos técnicos estándar o experiencia intermedia."
    else:
        level = "Baja Viabilidad (Alta Experiencia)"
        summary = "Posición competitiva que exige amplia trayectoria o cargos de dirección."

    return {
        "score": final_viability,
        "level": level,
        "summary": summary,
        "reasons": reasons[:3]
    }

def score_job_match(title: str, desc: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    text = f"{title} {desc}".lower()
    title_lower = title.lower()
    
    # 1. Negative keywords filter
    for neg in profile.get("negative_keywords", []):
        if neg.lower() in title_lower:
            return {
                "score": 0,
                "is_match": False,
                "reason": f"Descartado por coincidencia con '{neg}'."
            }

    # 2. Score positive skills
    score = 40
    matches = []
    for skill in profile.get("positive_skills", []):
        skill_lower = skill.lower()
        if skill_lower in title_lower:
            score += 15
            matches.append(skill)
        elif skill_lower in text:
            score += 6
            matches.append(skill)

    final_score = min(98, max(25, score))
    
    if matches:
        top_matches = list(dict.fromkeys(matches))[:3]
        reason = f"Alta compatibilidad en: {', '.join(top_matches)}."
    else:
        reason = "Alineado con el área de búsqueda general."

    return {
        "score": final_score,
        "is_match": final_score >= 40,
        "reason": reason
    }

def is_valid_deep_job_url(url: str) -> bool:
    if not url or url == "#" or len(url) < 15:
        return False
    u = url.lower().strip().rstrip("/")
    generic_domains = [
        "https://www.linkedin.com/jobs",
        "https://co.computrabajo.com",
        "https://co.indeed.com",
        "https://www.google.com/search?q=jobs",
        "https://www.elempleo.com",
        "https://linkedin.com",
        "https://computrabajo.com"
    ]
    if u in generic_domains:
        return False
    return any(path in u for path in ["/view/", "/oferta", "/viewjob", "/rc/clk", "jk=", "currentjobid="])

def process_job_row(row: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    title = clean_text(row.get("title")) or "Sin título"
    company = clean_text(row.get("company")) or "Empresa confidencial"
    location = clean_text(row.get("location")) or "Colombia"
    desc = clean_text(row.get("description"))
    
    direct_url = clean_text(row.get("job_url_direct"))
    standard_url = clean_text(row.get("job_url"))
    job_url = direct_url if is_valid_deep_job_url(direct_url) else standard_url
    
    site = (clean_text(row.get("site")) or "Web").capitalize()
    date_posted = clean_text(row.get("date_posted")) or "Reciente"
    
    salary_info = extract_salary_info(row)
    modality = detect_modality(title, desc, location, row.get("is_remote"))
    schedule = detect_schedule(clean_text(row.get("job_type")), desc)
    requirements = extract_key_requirements(desc, row.get("raw_bullets"))
    match_data = score_job_match(title, desc, profile)
    viability_data = calculate_viability(title, desc, profile)
    competition_data = estimate_competition(date_posted, desc, title)
    
    has_valid_url = is_valid_deep_job_url(job_url)
    
    return {
        "id": str(row.get("id") or hash(f"{title}_{company}_{location}")),
        "title": title,
        "company": company,
        "location": location,
        "site": site,
        "date_posted": date_posted,
        "job_url": job_url if has_valid_url else "",
        "has_direct_link": has_valid_url,
        "salary": salary_info,
        "modality": modality,
        "jornada": schedule["jornada"],
        "turno": schedule["turno"],
        "requirements": requirements,
        "match_score": match_data["score"],
        "match_reason": match_data["reason"],
        "viability_score": viability_data["score"],
        "viability_level": viability_data["level"],
        "viability_summary": viability_data["summary"],
        "viability_reasons": viability_data["reasons"],
        "competition_score": competition_data["score"],
        "competition_level": competition_data["level"],
        "competition_badge": competition_data["badge"],
        "competition_reason": competition_data["reason"],
        "is_temporary": any(w in (title + desc).lower() for w in ["vacaciones", "temporada", "temporal", "freelance", "obra o labor"]),
        "is_match": match_data["is_match"] and has_valid_url,
        "description_full": desc
    }
