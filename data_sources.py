"""Źródła danych wejściowych dla generatora publikacji."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pandas as pd

from data_schema import EXPECTED_COLUMNS


def load_excel(path: str) -> pd.DataFrame:
    """Wczytuje arkusz Excel."""
    return pd.read_excel(path)


def load_json(location: str) -> pd.DataFrame:
    """Wczytuje tablicę rekordów JSON z pliku lub chronionego URL-a.

    Akceptowane są ``[{...}]``, ``{"data": [{...}]}`` oraz odpowiedź
    Supabase ``[{"rekord": {...}}]``. Dla zdalnego źródła klucz API jest
    pobierany wyłącznie ze zmiennej środowiskowej ``DATA_SOURCE_API_KEY``.
    """
    if location.startswith(("https://", "http://")):
        headers = {
            "Accept": "application/json",
            "Accept-Profile": os.getenv("DATA_SOURCE_SUPABASE_SCHEMA", "dane_gov_api"),
        }
        api_key = os.getenv("DATA_SOURCE_API_KEY", "").strip()
        if api_key:
            headers["apikey"] = api_key
        request = Request(location, headers=headers)
        try:
            with urlopen(request, timeout=30) as response:  # noqa: S310 - URL jest konfiguracją operatora
                payload = json.load(response)
        except HTTPError as error:
            # Supabase zwraca w treści bezpieczny komunikat diagnostyczny, np.
            # "Invalid API key" albo "permission denied for ...". Nie pokazujemy
            # URL-a ani nagłówków żądania, ponieważ pochodzą z GitHub Secrets.
            response_body = error.read().decode("utf-8", errors="replace").strip()
            detail = response_body[:1000] if response_body else error.reason
            raise RuntimeError(
                f"Endpoint danych odrzucił żądanie (HTTP {error.code}): {detail}"
            ) from error
    else:
        with Path(location).open(encoding="utf-8") as source:
            payload = json.load(source)

    records = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValueError("JSON musi być tablicą rekordów lub obiektem z tablicą w polu 'data'.")

    if records and all(
        isinstance(row, dict) and isinstance(row.get("rekord"), dict)
        for row in records
    ):
        records = [row["rekord"] for row in records]

    if not records:
        # Pusta, ale poprawnie odczytana lista oznacza brak dostępnych lokali.
        # Zachowujemy pełny schemat, aby powstał CSV zawierający same nagłówki.
        return pd.DataFrame(columns=EXPECTED_COLUMNS)
    frame = pd.DataFrame.from_records(records)
    if set(frame.columns) == set(EXPECTED_COLUMNS):
        # Obiekty jsonb nie gwarantują kolejności kluczy. CSV zawsze musi mieć
        # kolejność kolumn określoną przez obowiązujący schemat.
        frame = frame.reindex(columns=EXPECTED_COLUMNS)
    return frame


def load_source(source_type: str, location: str) -> pd.DataFrame:
    """Wczytuje skonfigurowane źródło danych."""
    normalized_type = source_type.strip().lower()
    if normalized_type == "excel":
        return load_excel(location)
    if normalized_type == "json":
        return load_json(location)
    raise ValueError(f"Nieobsługiwany typ źródła: {source_type!r}. Dozwolone: excel, json.")
