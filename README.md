# Publikacja cen mieszkań Kerim

Repozytorium automatyzuje codzienną publikację danych o cenach mieszkań spółki
Kerim dla portalu dane.gov.pl. Źródłem bieżących danych jest chroniony endpoint
Supabase, a publiczne pliki CSV, XML i MD5 są udostępniane przez GitHub Pages.

## Jak działa publikacja

1. GitHub Actions uruchamia workflow codziennie o `00:17` czasu polskiego.
2. Generator pobiera rekordy JSON z widoku Supabase.
3. Dane są tłumaczone do oficjalnego schematu 48 kolumn i walidowane.
4. Powstaje niezmienny plik `csv/<rok>/Kerim-ceny-mieszkan-RRRR-MM-DD.csv`.
5. XML jest przebudowywany na podstawie wszystkich historycznych CSV.
6. Dane.gov.pl pobiera XML, MD5 oraz wskazane w XML-u zasoby CSV.

Istniejący dzienny CSV nigdy nie jest nadpisywany. Awaria źródła lub błędny
schemat zatrzymują publikację i pozostawiają ostatni poprawny stan bez zmian.

## Struktura repozytorium

| Ścieżka | Przeznaczenie |
| --- | --- |
| `excel_to_xml.py` | Główny generator CSV, XML i MD5 |
| `data_sources.py` | Pobieranie i normalizacja danych z Excela lub JSON-u |
| `data_schema.py` | Oficjalny schemat 48 kolumn i jego walidacja |
| `test_excel_to_xml.py` | Testy generatora i integracji modelu danych |
| `.github/workflows/main.yml` | Harmonogram i konfiguracja publikacji |
| `csv/<rok>/` | Niezmienne, dzienne zasoby publiczne |
| `history/` | Archiwalny XML i MD5 poprzedniej wersji zbioru |
| `docs/` | Architektura, podstawa prawna i lista weryfikacyjna |

Plik `Kerim_Dane_ceny_mieszkan_nowa_struktura.xlsx` pozostaje lokalnym źródłem
awaryjnym i wzorem obowiązującego układu. `Kerim_Dane_ceny_mieszkan.xlsx` jest
kopią poprzedniej struktury.

## Konfiguracja GitHub Actions

Workflow wymaga dwóch sekretów repozytorium:

| Sekret | Wartość |
| --- | --- |
| `DANE_GOV_SUPABASE_URL` | Pełny URL widoku REST, np. `/rest/v1/oferty?select=rekord` |
| `DANE_GOV_SUPABASE_PUBLISHABLE_KEY` | Klucz Supabase `sb_publishable_...` |

Sekrety są przekazywane wyłącznie jako zmienne środowiskowe. Generator nie
wypisuje URL-a ani klucza w logach.

## Kontrakt danych aplikacji

Endpoint zwraca tablicę w formacie:

```json
[
  {
    "rekord": {
      "Firma": "KeriM Sp. z o.o.",
      "Pomieszczenia przynależne": [],
      "Prawa niezbędne do korzystania": [],
      "Inne świadczenia pieniężne": []
    }
  }
]
```

Każda z trzech sekcji zagnieżdżonych może być pusta albo zawierać maksymalnie
jeden obiekt z kompletem oficjalnych pól tej sekcji. Nieznane lub brakujące
pola oraz drugi element zatrzymują publikację. Pusta sekcja jest zapisywana w
CSV jako `X`.

W płaskim modelu JSON pominięte pola, `null` i puste teksty są awaryjnie
zamieniane na `X`. Ceny i wartości pieniężne są zapisywane z dwoma miejscami
po przecinku; prawdziwa wartość `0` pozostaje kwotą `0.00`.

## Uruchomienie lokalne

Domyślnie generator korzysta z lokalnego Excela:

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -v
python excel_to_xml.py
```

Test lokalnego JSON-u:

```powershell
$env:DATA_SOURCE_TYPE = "json"
$env:DATA_SOURCE_LOCATION = "C:\sciezka\dane.json"
python excel_to_xml.py
```

Obsługiwane zmienne środowiskowe:

| Zmienna | Znaczenie |
| --- | --- |
| `DATA_SOURCE_TYPE` | `excel` albo `json` |
| `DATA_SOURCE_LOCATION` | Ścieżka lokalna lub URL HTTPS |
| `DATA_SOURCE_API_KEY` | Klucz API dla zdalnego źródła |
| `DATA_SOURCE_SUPABASE_SCHEMA` | Schemat Supabase; domyślnie `dane_gov_api` |
| `PUBLIC_BASE_URL` | Publiczny bazowy URL zasobów; domyślnie GitHub Pages |

## Utrzymanie i awarie

- Pusta tablica JSON oznacza potwierdzony brak dostępnych lokali i tworzy CSV
  zawierający wyłącznie nagłówki.
- Błąd HTTP, uszkodzony JSON lub niezgodny schemat przerywa workflow.
- Po nieudanym uruchomieniu nie należy kopiować poprzedniego CSV z nową datą.
- Ręczne uruchomienie: **Actions → Publikacja danych dla dane.gov.pl → Run workflow**.
- Po zmianie struktury prawnej należy najpierw zaktualizować schemat i testy,
  a następnie wykonać kontrolny run bez nadpisywania istniejącego CSV.

Szczegółowe decyzje techniczne opisuje [dokument architektury](docs/ARCHITEKTURA.md).
Lista tematów wymagających okresowej kontroli znajduje się w
[liście weryfikacyjnej](docs/DO_WERYFIKACJI.md).

## Podstawa prawna

Zasoby od 11 listopada 2026 r. stosują strukturę określoną w rozporządzeniu
Ministra Cyfryzacji z 10 listopada 2026 r. (Dz. U. z 2026 r. poz. 1489).
Kopia dokumentu znajduje się w `docs/podstawa-prawna/`.
