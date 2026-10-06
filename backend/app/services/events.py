"""Supporto agli eventi: ora italiana, etichette delle date in italiano."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

_DAYS = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
_MONTHS = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto",
           "settembre", "ottobre", "novembre", "dicembre"]


def _last_sunday(year: int, month: int) -> datetime:
    d = datetime(year, month + 1, 1) - timedelta(days=1) if month < 12 else datetime(year, 12, 31)
    return d - timedelta(days=(d.weekday() - 6) % 7)


def rome_now(utc_now: Optional[datetime] = None) -> datetime:
    """Ora italiana senza fuso (ora legale dall'ultima domenica di marzo all'ultima di ottobre, alle 01:00 UTC).
    Calcolata a mano: su Windows il database dei fusi orari spesso non e' installato."""
    now = utc_now or datetime.now(timezone.utc).replace(tzinfo=None)
    summer_start = _last_sunday(now.year, 3).replace(hour=1)
    summer_end = _last_sunday(now.year, 10).replace(hour=1)
    offset = 2 if summer_start <= now < summer_end else 1
    return now + timedelta(hours=offset)


def event_end(d: Dict[str, Any]) -> datetime:
    """Fine di una data: se non indicata, l'evento vale fino a fine giornata."""
    if d.get("end"):
        return d["end"]
    return d["start"].replace(hour=23, minute=59)


def date_label(d: Dict[str, Any]) -> str:
    """"sabato 18 ottobre 2026, ore 18:00–21:00" oppure "dal 18 al 20 ottobre 2026"."""
    start, end = d["start"], d.get("end")
    day = f"{_DAYS[start.weekday()]} {start.day} {_MONTHS[start.month - 1]} {start.year}"
    has_time = (start.hour, start.minute) != (0, 0)
    if end and end.date() != start.date():
        if end.year == start.year and end.month == start.month:
            return f"dal {start.day} al {end.day} {_MONTHS[end.month - 1]} {end.year}"
        return f"dal {start.day} {_MONTHS[start.month - 1]} al {end.day} {_MONTHS[end.month - 1]} {end.year}"
    if not has_time:
        return day
    label = f"{day}, ore {start:%H:%M}"
    if end and end > start:
        label += f"–{end:%H:%M}"
    return label


def upcoming_dates(dates: List[Dict[str, Any]], now: Optional[datetime] = None) -> List[Dict[str, Any]]:
    now = now or rome_now()
    return [d for d in dates if event_end(d) >= now]
