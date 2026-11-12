# Architektura publikacji danych

## Przepływ

1. GitHub Actions uruchamia generator raz dziennie.
2. Generator pobiera JSON z widoku `dane_gov_api.oferty` w Supabase.
3. Model aplikacji jest normalizowany i przechodzi walidację schematu 48 kolumn.
4. Powstaje niezmienny CSV w `csv/<rok>/`.
5. XML jest budowany ze wszystkich istniejących dziennych CSV.
6. Portal dane.gov.pl pobiera XML, MD5 i wskazane w nim zasoby.

Lokalny Excel pozostaje źródłem awaryjnym. Źródło danych i miejsce publikacji
CSV są od siebie niezależne, dzięki czemu przyszła migracja plików publicznych
do R2 nie wymaga zmiany modelu danych.

## Granice odpowiedzialności

- Supabase przechowuje dane biznesowe i wystawia publiczny widok tylko do odczytu.
- `data_sources.py` odpowiada za transport i translację modelu aplikacji.
- `data_schema.py` jest jedynym źródłem prawdy dla kolejności kolumn CSV.
- `excel_to_xml.py` tworzy niezmienny dzienny CSV oraz indeks XML i MD5.
- GitHub Pages udostępnia wyłącznie publiczne rezultaty publikacji.

Sekcja zagnieżdżona może zawierać maksymalnie jeden element. Nieznane pola,
brak wymaganych pól albo większa liczba elementów kończą workflow błędem zamiast
powodować cichą utratę danych.

## Polityka awaryjna

Transport i stan biznesowy nie są tym samym:

- poprawnie odczytane `{"data": []}` oznacza potwierdzony brak dostępnych
  lokali i powoduje utworzenie CSV zawierającego same nagłówki;
- brak odpowiedzi, błąd HTTP, brak pliku, uszkodzony JSON albo błędny schemat
  oznacza awarię źródła i zatrzymuje publikację;
- podczas awarii nie tworzymy kopii poprzedniego CSV z nową datą, ponieważ
  sugerowałaby ona, że nieaktualne dane zostały potwierdzone tego dnia;
- istniejące CSV, XML i MD5 nie są usuwane ani nadpisywane przez nieudaną
  publikację. Na portalu pozostaje ostatni poprawny stan.

## Cloudflare R2

Najprostszy etap przejściowy to przechowywanie w R2 wyłącznie JSON-u aplikacji.
Generator pobiera go przez HTTPS, a CSV nadal publikuje przez GitHub Pages.
Przeniesienie CSV do R2 wymaga później dodania mechanizmu wysyłania obiektów
oraz zmiany `PUBLIC_BASE_URL`; generowanie danych i XML pozostaje bez zmian.
