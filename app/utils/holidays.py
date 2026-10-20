"""PC est magique - Zone C (ESPCI) School Holidays & Reservation Return Date Utilities"""

from __future__ import annotations

from dataclasses import dataclass
import datetime
import logging
import zoneinfo

import cachetools
import requests


_API_URL = (
    "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/"
    "fr-en-calendrier-scolaire/records"
)
_PARIS_TZ = zoneinfo.ZoneInfo("Europe/Paris")
_holidays_cache: cachetools.TTLCache = cachetools.TTLCache(maxsize=4, ttl=86400)


@dataclass(frozen=True)
class EspciVacation:
    """An ESPCI vacation period derived from Zone C school holidays.

    Attributes:
        title: Display name of the holiday (e.g. 'Vacances de la Toussaint').
        start_date: First day of the ESPCI vacation (Saturday).
        end_date: Monday marking the end of the vacation (classes resume).
    """

    title: str
    start_date: datetime.date
    end_date: datetime.date

    @property
    def friday_before(self) -> datetime.date:
        """Return the Friday immediately preceding the vacation."""
        return self.start_date - datetime.timedelta(days=1)


def get_espci_vacations(min_year: int = 2024) -> list[EspciVacation]:
    """Return ESPCI vacations, cached for 24h. Failed fetches are never cached."""
    try:
        return _get_espci_vacations_cached(min_year)
    except requests.RequestException as exc:
        logging.warning(f"Could not fetch Zone C school holidays: {exc}")
        return []


@cachetools.cached(_holidays_cache)
def _get_espci_vacations_cached(min_year: int) -> list[EspciVacation]:
    """Fetch Zone C (Paris) school holidays and apply ESPCI rules.

    ESPCI students have:
    - Both weeks for Christmas ('Vacances de Noël').
    - Only the second week for Toussaint, Hiver, and Printemps vacations.
    """
    vacations: list[EspciVacation] = []
    resp = requests.get(
        _API_URL,
        params={
            "where": (
                f'location="Paris" AND population!="Enseignants" '
                f'AND end_date >= "{min_year}-01-01"'
            ),
            "order_by": "start_date ASC",
            "limit": 100,
        },
        timeout=5,
    )
    resp.raise_for_status()
    records = resp.json().get("results", [])

    seen: set[tuple[str, datetime.date]] = set()
    for rec in records:
        desc = (rec.get("description") or "").strip()
        desc_lower = desc.lower()
        if not desc_lower.startswith("vacances") or "été" in desc_lower or "ete" in desc_lower:
            continue

        try:
            raw_start = (
                datetime.datetime.fromisoformat(rec["start_date"])
                .astimezone(_PARIS_TZ)
                .date()
            )
            raw_end = (
                datetime.datetime.fromisoformat(rec["end_date"])
                .astimezone(_PARIS_TZ)
                .date()
            )
        except (KeyError, ValueError):
            continue

        if (raw_end - raw_start).days < 10:
            continue

        is_christmas = "noël" in desc_lower or "noel" in desc_lower
        effective_start = (
            raw_start if is_christmas else raw_start + datetime.timedelta(days=7)
        )
        # Ensure end_date is the Monday marking the end of the vacation
        return_monday = raw_end - datetime.timedelta(days=raw_end.weekday())

        if effective_start >= return_monday:
            continue

        key = (desc, effective_start)
        if key in seen:
            continue
        seen.add(key)

        vacations.append(
            EspciVacation(
                title=desc,
                start_date=effective_start,
                end_date=return_monday,
            )
        )

    return vacations


def compute_jeu_return_date(from_date: datetime.date | None = None) -> datetime.date:
    """Compute the mandatory return date for a game reserved on `from_date`.

    Rules:
    - If `from_date` is the Friday before an ESPCI vacation or during an ESPCI
      vacation, the game must be returned on the Monday marking the end of that
      vacation.
    - If `from_date` is a Friday, Saturday, or Sunday, the game must be returned
      on the following Monday.
    - If `from_date` is Monday through Thursday, the game must be returned the
      following day.
    """
    today = from_date or datetime.date.today()

    for vac in get_espci_vacations(min_year=today.year - 1):
        if vac.friday_before <= today < vac.end_date:
            return vac.end_date

    weekday = today.weekday() 
    if weekday >= 4: # Weekday past Friday
        return today + datetime.timedelta(days=7 - weekday)
    return today + datetime.timedelta(days=1)
