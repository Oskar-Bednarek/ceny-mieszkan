# ceny-mieszkan
Automatyzacja danych dla portalu dane.gov.pl

Generator wczytuje dane z `Kerim_Dane_ceny_mieszkan_nowa_struktura.xlsx` i
zapisuje codzienny, niezmienny stan jako CSV w katalogu `csv/<rok>`. Istniejący
CSV dla danej daty nigdy nie jest nadpisywany.

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

JSON może być tablicą rekordów albo obiektem `{"data": [...]}`. Nazwy i
kolejność wszystkich 48 pól są walidowane przed utworzeniem CSV. Oznacza to,
że przyszła aplikacja może wystawić dane jako publiczny JSON w Cloudflare R2,
a przełączenie generatora będzie wymagało tylko konfiguracji workflow.

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
