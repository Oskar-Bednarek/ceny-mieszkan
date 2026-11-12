"""Źródła danych wejściowych dla generatora publikacji."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pandas as pd

from data_schema import EXPECTED_COLUMNS


COLUMN_ALIASES = {
    "Numer identyfikacji podatkowej (NIP)": "Numer Identyfikacji Podatkowej (NIP)",
    **{
        f"{prefix} adresu siedziby albo głównego miejsca wykonywania działalności gospodarczej":
        f"{prefix} adresu siedziby albo głównego miejsca wykonywania działalności"
        for prefix in (
            "Województwo", "Powiat", "Gmina", "Miejscowość", "Ulica",
            "Numer nieruchomości", "Numer lokalu", "Kod pocztowy",
        )
    },
    "Długość geograficzna punktu określającego lokalizację przedsięwzięcia deweloperskiego lub zadania inwestycyjnego":
        "Długość geograficzna punktu określającego lokalizację przestrzenną przedsięwzięcia deweloperskiego albo zadania inwestycyjnego",
    "Szerokość geograficzna punktu określającego lokalizację przedsięwzięcia deweloperskiego lub zadania inwestycyjnego":
        "Szerokość geograficzna punktu określającego lokalizację przestrzenną przedsięwzięcia deweloperskiego albo zadania inwestycyjnego",
    "Data i czas, od których obowiązuje cena lokalu mieszkalnego albo domu jednorodzinnego lub ich części będących przedmiotem umowy":
        "Data i czas, od których obowiązuje cena lokalu mieszkalnego albo domu jednorodzinnego lub ich części",
}

NESTED_SECTIONS = {
    "Pomieszczenia przynależne": EXPECTED_COLUMNS[35:40],
    "Prawa niezbędne do korzystania": EXPECTED_COLUMNS[40:44],
    "Inne świadczenia pieniężne": EXPECTED_COLUMNS[44:48],
}


def _as_items(section_name: str, value: object) -> list[dict]:
    """Normalizuje opcjonalną sekcję aplikacji do listy obiektów."""
    if value in (None, "", "X"):
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        if len(value) > 1:
            raise ValueError(
                f"Sekcja {section_name!r} może zawierać najwyżej jeden element."
            )
        return value
    raise ValueError(
        f"Sekcja {section_name!r} musi być obiektem, tablicą obiektów albo pusta."
    )


def _normalize_app_record(record: dict) -> list[dict]:
    """Zamienia model aplikacji na płaskie wiersze oficjalnego CSV."""
    base = {
        COLUMN_ALIASES.get(key, key): value
        for key, value in record.items()
        if key not in NESTED_SECTIONS
    }
    if not any(name in record for name in NESTED_SECTIONS):
        return [base]

    sections = {
        name: _as_items(name, record.get(name))
        for name in NESTED_SECTIONS
    }
    row_count = max((len(items) for items in sections.values()), default=0) or 1
    rows = []
    for index in range(row_count):
        row = dict(base)
        for section_name, columns in NESTED_SECTIONS.items():
            items = sections[section_name]
            has_item = index < len(items)
            item = items[index] if has_item else {}
            normalized_item = {COLUMN_ALIASES.get(key, key): value for key, value in item.items()}
            if has_item and set(normalized_item) != set(columns):
                missing = sorted(set(columns) - set(normalized_item))
                extra = sorted(set(normalized_item) - set(columns))
                details = []
                if missing:
                    details.append(f"brakujące pola: {missing}")
                if extra:
                    details.append(f"nieznane pola: {extra}")
                raise ValueError(
                    f"Nieprawidłowa sekcja {section_name!r} ({'; '.join(details)})."
                )
            for column in columns:
                row[column] = normalized_item.get(column, "X")
        rows.append(row)
    return rows


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
    normalized_records = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Każdy rekord JSON musi być obiektem.")
        normalized_records.extend(_normalize_app_record(record))

    frame = pd.DataFrame.from_records(normalized_records)
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
