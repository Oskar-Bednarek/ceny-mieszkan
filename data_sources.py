"""Źródła danych wejściowych dla generatora publikacji."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.request import urlopen

import pandas as pd


def load_excel(path: str) -> pd.DataFrame:
    """Wczytuje arkusz Excel."""
    return pd.read_excel(path)


def load_json(location: str) -> pd.DataFrame:
    """Wczytuje tablicę rekordów JSON z pliku lub publicznego URL-a.

    Akceptowane są zarówno ``[{...}]``, jak i ``{"data": [{...}]}``.
    Dzięki obsłudze HTTPS źródłem może być publiczny obiekt Cloudflare R2.
    """
    if location.startswith(("https://", "http://")):
        with urlopen(location, timeout=30) as response:  # noqa: S310 - URL jest konfiguracją operatora
            payload = json.load(response)
    else:
        with Path(location).open(encoding="utf-8") as source:
            payload = json.load(source)

    records = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValueError("JSON musi być tablicą rekordów lub obiektem z tablicą w polu 'data'.")
    return pd.DataFrame.from_records(records)


def load_source(source_type: str, location: str) -> pd.DataFrame:
    """Wczytuje skonfigurowane źródło danych."""
    normalized_type = source_type.strip().lower()
    if normalized_type == "excel":
        return load_excel(location)
    if normalized_type == "json":
        return load_json(location)
    raise ValueError(f"Nieobsługiwany typ źródła: {source_type!r}. Dozwolone: excel, json.")
