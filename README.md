# ceny-mieszkan
Automatyzacja danych dla portalu dane.gov.pl

Generator w GitHub Actions wczytuje dane z chronionego endpointu Supabase i
zapisuje codzienny, niezmienny stan jako CSV w katalogu `csv/<rok>`. Istniejący
CSV dla danej daty nigdy nie jest nadpisywany. Lokalnie domyślnym źródłem
pozostaje `Kerim_Dane_ceny_mieszkan_nowa_struktura.xlsx`.

Główny plik `kerim-ceny-mieszkan.xml` zawiera jeden zbiór danych i wszystkie
historyczne oraz przyszłe pliki CSV znalezione w katalogu `csv`. Rozpoczęcie
nowego roku nie wymaga zmiany konfiguracji.

Plik `Kerim_Dane_ceny_mieszkan.xlsx` pozostaje w repozytorium jako kopia
poprzedniego schematu danych.

## Źródło danych

Domyślnie generator czyta plik Excel. Źródło można zmienić bez modyfikowania
kodu, ustawiając zmienne środowiskowe:

- `DATA_SOURCE_TYPE` — `excel` (domyślnie) albo `json`,
- `DATA_SOURCE_LOCATION` — ścieżka lokalna albo, dla JSON-u, publiczny URL HTTPS,
- `PUBLIC_BASE_URL` — bazowy adres opublikowanych plików CSV.

JSON może być tablicą rekordów, obiektem `{"data": [...]}` albo odpowiedzią
Supabase `[{"rekord": {...}}]`. Nazwy wszystkich 48 pól są walidowane przed
utworzeniem CSV, a kolejność jest normalizowana do oficjalnego schematu.

Workflow korzysta z sekretów repozytorium:

- `DANE_GOV_SUPABASE_URL` — pełny URL endpointu REST,
- `DANE_GOV_SUPABASE_PUBLISHABLE_KEY` — publishable key przesyłany w nagłówku
  `apikey`.

Wartości sekretów nie mogą być wpisywane do kodu ani wypisywane w logach.

Przykład lokalny:

```powershell
$env:DATA_SOURCE_TYPE = "json"
$env:DATA_SOURCE_LOCATION = "https://dane.example.pl/ceny.json"
python excel_to_xml.py
```

## Brak danych i awarie źródła

- Poprawna odpowiedź JSON z pustą tablicą (`{"data": []}`) oznacza brak
  dostępnych lokali. Generator publikuje wtedy CSV zawierający same nagłówki.
- Brak pliku, błąd HTTP, uszkodzony JSON lub nieprawidłowy schemat zatrzymuje
  publikację. Nie powstaje zasób z fałszywą datą, a ostatni poprawny zasób
  pozostaje dostępny.
- Generator nigdy nie nadpisuje istniejącego dziennego CSV.

Opis przepływu i decyzji awaryjnych znajduje się w
[`docs/ARCHITEKTURA.md`](docs/ARCHITEKTURA.md).
