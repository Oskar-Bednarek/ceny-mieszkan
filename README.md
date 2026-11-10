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
