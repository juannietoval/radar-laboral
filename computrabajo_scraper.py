import re
import urllib.parse
from typing import List, Dict, Any, Optional
import requests
from lxml import html
import json
from concurrent.futures import ThreadPoolExecutor

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def clean_url_term(term: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', term)
    cleaned = re.sub(r'\s+', '-', cleaned).strip('-').lower()
    return cleaned

def enrich_offer_detail(job: Dict[str, Any]) -> Dict[str, Any]:
    url = job.get('job_url')
    if not url or not url.startswith('http'):
        return job
    try:
        r = requests.get(url, headers=HEADERS, timeout=7)
        if r.status_code != 200:
            return job
        
        if r.url and r.url.startswith('http') and not '#' in r.url:
            job['job_url'] = r.url
            job['job_url_direct'] = r.url
            
        tree = html.fromstring(r.text)
        
        job_ld = None
        for s in tree.xpath('//script[@type="application/ld+json"]/text()'):
            try:
                d = json.loads(s)
                if d.get('@type') == 'JobPosting':
                    job_ld = d
                    break
                elif '@graph' in d:
                    for it in d['@graph']:
                        if it.get('@type') == 'JobPosting':
                            job_ld = it
                            break
            except Exception:
                pass
                
        if job_ld:
            base_sal = job_ld.get('baseSalary')
            if isinstance(base_sal, dict):
                val_obj = base_sal.get('value', {})
                if isinstance(val_obj, dict) and val_obj.get('value'):
                    job['min_amount'] = float(val_obj.get('value'))
                    job['max_amount'] = float(val_obj.get('value'))
                    job['currency'] = base_sal.get('currency', 'COP')
                elif isinstance(val_obj, (int, float)):
                    job['min_amount'] = float(val_obj)
                    job['max_amount'] = float(val_obj)
                    job['currency'] = base_sal.get('currency', 'COP')
            
            raw_desc = job_ld.get('description', '')
            if raw_desc:
                desc_text = re.sub(r'<[^>]+>', ' ', raw_desc)
                desc_text = re.sub(r'\s+', ' ', desc_text).strip()
                job['description'] = desc_text
                
            emp_type = job_ld.get('employmentType')
            if emp_type:
                job['job_type'] = "Tiempo Completo" if "FULL_TIME" in str(emp_type) else str(emp_type)
        
        badges = tree.xpath('//div[contains(@class, "fs16")]//span/text() | //span[contains(@class, "tag")]/text()')
        badge_texts = [b.strip() for b in badges if b.strip()]
        for b in badge_texts:
            if "$" in b and job.get('min_amount') is None:
                clean_b = b.replace("$", "").strip().split()[0]
                clean_b = clean_b.replace(".", "").replace(",", ".")
                try:
                    v = float(clean_b)
                    if 500000 <= v <= 60000000:
                        job['min_amount'] = v
                        job['max_amount'] = v
                        job['currency'] = 'COP'
                except Exception:
                    pass
            if any(w in b.lower() for w in ["completo", "medio tiempo", "obra o labor", "fijo", "indefinido", "aprendizaje", "prácticas"]):
                job['job_type'] = b
                
        body_nodes = tree.xpath('//p[contains(@class, "mbB")]//text() | //div[contains(@class, "box_detail")]//p//text()')
        if body_nodes:
            full_body = " ".join([b.strip() for b in body_nodes if b.strip() and not b.strip().startswith('Ocultaste')])
            if len(full_body) > len(job.get('description', '')):
                job['description'] = full_body

        req_bullets = tree.xpath('//div[contains(@class, "box_detail")]//ul[contains(@class, "disc")]//li/text()')
        cleaned_bullets = [rb.strip() for rb in req_bullets if rb.strip() and len(rb.strip()) > 3]
        if cleaned_bullets:
            job['raw_bullets'] = cleaned_bullets

    except Exception:
        pass

    return job

def scrape_computrabajo(
    query: str,
    location: str = "risaralda",
    max_pages: int = 2,
    max_results: int = 30
) -> List[Dict[str, Any]]:
    jobs = []
    slug_query = clean_url_term(query)
    seen_urls = set()

    loc_lower = location.lower()
    is_remote_search = "remoto" in loc_lower or "teletrabajo" in loc_lower or "virtual" in loc_lower or "remoto" in query.lower()
    is_risaralda = "risaralda" in loc_lower or "pereira" in loc_lower or "pereira" in query.lower() or "risaralda" in query.lower()

    if is_risaralda:
        base_url = f"https://co.computrabajo.com/trabajo-de-{slug_query}-en-risaralda"
    elif is_remote_search:
        base_url = f"https://co.computrabajo.com/trabajo-de-{slug_query}-con-teletrabajo"
    else:
        base_url = f"https://co.computrabajo.com/trabajo-de-{slug_query}"

    for page in range(1, max_pages + 1):
        if len(jobs) >= max_results:
            break
            
        page_url = f"{base_url}?p={page}" if page > 1 else base_url
        try:
            r = requests.get(page_url, headers=HEADERS, timeout=10)
            if r.status_code != 200:
                break
            
            tree = html.fromstring(r.text)
            articles = tree.xpath('//article[contains(@class, "box_offer")]')
            if not articles:
                break
                
            for art in articles:
                if len(jobs) >= max_results:
                    break

                title_nodes = art.xpath('.//h2//a | .//a[contains(@class, "js-o-link")]')
                if not title_nodes:
                    continue
                title = title_nodes[0].text_content().strip()
                link = title_nodes[0].attrib.get('href', '')
                if not link:
                    continue
                if not link.startswith('http'):
                    link = 'https://co.computrabajo.com' + link.split('#')[0]

                if link in seen_urls:
                    continue
                seen_urls.add(link)

                company_nodes = art.xpath('.//p[contains(@class, "fs16")]//text() | .//p[contains(@class, "fc_base")]//text()')
                clean_company = [c.strip() for c in company_nodes if c.strip() and not re.match(r'^\d,\d$', c.strip())]
                company = clean_company[0] if clean_company else "Empresa Confidencial"
                
                loc_nodes = art.xpath('.//p[contains(@class, "fs13")]//text() | .//span[contains(@class, "fs13")]//text()')
                loc_texts = [l.strip() for l in loc_nodes if l.strip()]
                job_location = "Pereira, Risaralda" if is_risaralda else "Colombia (Remoto)" if is_remote_search else "Colombia"
                for t in loc_texts:
                    if any(city in t.lower() for city in ["pereira", "dosquebradas", "risaralda", "bogotá", "medellín", "cali", "manizales", "teletrabajo", "desde casa"]):
                        job_location = t
                        break

                date_posted = "Reciente"
                for t in loc_texts:
                    if "hace" in t.lower() or "ayer" in t.lower() or "hoy" in t.lower():
                        date_posted = t
                        break

                snippet_nodes = art.xpath('.//p[contains(@class, "break")]//text() | .//p[contains(@class, "fc_aux")]//text()')
                snippet = " ".join([s.strip() for s in snippet_nodes if s.strip()])
                
                is_remote_flag = is_remote_search or "remoto" in (title + snippet + job_location).lower() or "teletrabajo" in (title + snippet + job_location).lower() or "desde casa" in (title + snippet).lower()

                jobs.append({
                    "id": f"comp_{abs(hash(link))}",
                    "site": "Computrabajo",
                    "title": title,
                    "company": company,
                    "location": job_location,
                    "date_posted": date_posted,
                    "job_url": link,
                    "job_url_direct": link,
                    "min_amount": None,
                    "max_amount": None,
                    "currency": "COP",
                    "interval": "monthly",
                    "is_remote": is_remote_flag,
                    "job_type": "Tiempo Completo",
                    "description": f"{title}. {snippet}. Ubicación: {job_location}."
                })
        except Exception:
            break

    if jobs:
        with ThreadPoolExecutor(max_workers=8) as executor:
            enriched_jobs = list(executor.map(enrich_offer_detail, jobs))
        return enriched_jobs

    return jobs
