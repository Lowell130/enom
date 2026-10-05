import re
import unicodedata
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Deque, Dict

from fastapi import HTTPException, Request


def slugify(text: str) -> str:
    """Converte un testo in slug kebab-case (unica implementazione del progetto).
    Le lettere accentate perdono l'accento ("Vietènn" -> "vietenn"): gli indirizzi restano leggibili
    anche quando vengono condivisi."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


async def unique_slug(collection, base_slug: str, exclude_id=None) -> str:
    """Restituisce uno slug libero nella collezione aggiungendo -2, -3, ... se necessario."""
    base_slug = base_slug or "item"
    candidate = base_slug
    counter = 2
    while True:
        query = {"slug": candidate}
        if exclude_id is not None:
            query["_id"] = {"$ne": exclude_id}
        if not await collection.find_one(query, {"_id": 1}):
            return candidate
        candidate = f"{base_slug}-{counter}"
        counter += 1


def client_ip(request: Request) -> str:
    # Non si legge X-Forwarded-For direttamente (falsificabile dal client):
    # dietro un reverse proxy avviare uvicorn con --proxy-headers --forwarded-allow-ips.
    return request.client.host if request.client else "unknown"


class RateLimiter:
    """Limitatore a finestra scorrevole in memoria (per singolo processo)."""

    def __init__(self):
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _prune(self, key: str, window: int, now: float) -> Deque[float]:
        hits = self._hits[key]
        while hits and hits[0] <= now - window:
            hits.popleft()
        return hits

    def is_limited(self, key: str, limit: int, window: int) -> bool:
        with self._lock:
            return len(self._prune(key, window, time.monotonic())) >= limit

    def hit(self, key: str, window: int) -> None:
        with self._lock:
            now = time.monotonic()
            self._prune(key, window, now).append(now)

    def check_and_hit(self, key: str, limit: int, window: int, detail: str) -> None:
        with self._lock:
            now = time.monotonic()
            hits = self._prune(key, window, now)
            if len(hits) >= limit:
                raise HTTPException(status_code=429, detail=detail)
            hits.append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()


rate_limiter = RateLimiter()
