"""Estrazione dei dati di un vino da una pagina web pubblica, con protezione SSRF."""
import ipaddress
import re
import socket
from typing import Callable, Dict, Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException

MAX_REDIRECTS = 4
MAX_BYTES = 3 * 1024 * 1024  # 3 MB
TIMEOUT = (5, 12)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
}


def _is_public_ip(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped:
        addr = addr.ipv4_mapped
    return addr.is_global and not (
        addr.is_private or addr.is_loopback or addr.is_link_local
        or addr.is_multicast or addr.is_reserved or addr.is_unspecified
    )


def validate_public_url(url: str) -> str:
    """Accetta solo URL http(s) che risolvono esclusivamente verso IP pubblici."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(status_code=400, detail="URL non valido")
    if parsed.username or parsed.password:
        raise HTTPException(status_code=400, detail="URL non valido")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if port not in (80, 443, 8080, 8443):
        raise HTTPException(status_code=400, detail="Porta non consentita")
    try:
        infos = socket.getaddrinfo(parsed.hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise HTTPException(status_code=400, detail="Dominio non raggiungibile")
    ips = {info[4][0] for info in infos}
    if not ips or not all(_is_public_ip(ip) for ip in ips):
        raise HTTPException(status_code=400, detail="Indirizzo non consentito")
    return url


def fetch_public_html(url: str, validator: Callable[[str], str] = validate_public_url) -> str:
    session = requests.Session()
    session.headers.update(HEADERS)
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        validator(current)
        resp = session.get(current, timeout=TIMEOUT, allow_redirects=False, stream=True)
        if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location")
            resp.close()
            if not location:
                break
            current = urljoin(current, location)
            continue

        if resp.status_code in (401, 403):
            resp.close()
            raise HTTPException(
                status_code=400,
                detail="Il sito di destinazione applica protezioni anti-bot (Cloudflare/Wordfence). Inserisci i dettagli del vino manualmente o usa l'Estensione Chrome."
            )
        if resp.status_code != 200:
            resp.close()
            raise HTTPException(status_code=400, detail=f"Impossibile accedere alla pagina del vino (Errore HTTP {resp.status_code})")

        chunks, size = [], 0
        for chunk in resp.iter_content(64 * 1024):
            size += len(chunk)
            if size > MAX_BYTES:
                resp.close()
                raise HTTPException(status_code=400, detail="La pagina è troppo grande da analizzare")
            chunks.append(chunk)
        raw = b"".join(chunks)
        try:
            from charset_normalizer import from_bytes  # dipendenza di requests
            best = from_bytes(raw).best()
            if best is not None:
                return str(best)
        except Exception:
            pass
        return raw.decode(resp.encoding or "utf-8", errors="replace")

    raise HTTPException(status_code=400, detail="Troppi reindirizzamenti")


def parse_wine_page(html_text: str, clean_wine_title: Callable[[str], str]) -> Dict[str, Any]:
    soup = BeautifulSoup(html_text, 'html.parser')

    og_title = soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'og:title'})
    title_tag = soup.find('title')
    raw_title = og_title.get('content', '') if og_title else (title_tag.text if title_tag else '')
    name = clean_wine_title(raw_title)

    if any(k in name.lower() for k in ("403", "forbidden", "access denied")):
        raise HTTPException(
            status_code=400,
            detail="Il sito di destinazione applica protezioni anti-bot. Inserisci i dettagli del vino manualmente."
        )

    og_desc = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
    p_desc = soup.find('p')
    raw_desc = og_desc.get('content', '') if og_desc else (p_desc.text if p_desc else '')

    og_img = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'})
    photo_url = og_img.get('content', '') if og_img else ''
    if photo_url and not photo_url.startswith(("http://", "https://")):
        photo_url = ""

    lower_html = html_text.lower()

    category = "VINO_ROSSO"
    if "spumante" in lower_html or "brut" in lower_html:
        category = "SPUMANTE"
    elif "rosato" in lower_html or "rosé" in lower_html:
        category = "ROSATO"
    elif "bianco" in lower_html:
        category = "VINO_BIANCO"
    elif "passito" in lower_html:
        category = "PASSITO"

    denominazione = "DOC"
    if "igt" in lower_html and not ("tintilia" in lower_html or "biferno" in lower_html or "doc" in lower_html):
        denominazione = "IGT"

    alc_match = re.search(r'(\d{2}(?:[.,]\d)?)\s*%\s*(?:vol)?', lower_html)
    alcohol_degrees = float(alc_match.group(1).replace(',', '.')) if alc_match else None

    return {
        "name": name.strip(),
        "category": category,
        "denominazione": denominazione,
        "vintage_year": None,
        "is_riserva": "riserva" in lower_html,
        "alcohol_degrees": alcohol_degrees,
        "description": raw_desc.strip(),
        "photo_url": photo_url,
        "technical_sheet_pdf": ""
    }
