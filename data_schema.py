"""Walidacja struktury danych określonej rozporządzeniem z 10 listopada 2026 r."""

from __future__ import annotations

import pandas as pd


EXPECTED_COLUMNS = [
    "Firma",
    "Numer Identyfikacji Podatkowej (NIP)",
    "Województwo adresu siedziby albo głównego miejsca wykonywania działalności",
    "Powiat adresu siedziby albo głównego miejsca wykonywania działalności",
    "Gmina adresu siedziby albo głównego miejsca wykonywania działalności",
    "Miejscowość adresu siedziby albo głównego miejsca wykonywania działalności",
    "Ulica adresu siedziby albo głównego miejsca wykonywania działalności",
    "Numer nieruchomości adresu siedziby albo głównego miejsca wykonywania działalności",
    "Numer lokalu adresu siedziby albo głównego miejsca wykonywania działalności",
    "Kod pocztowy adresu siedziby albo głównego miejsca wykonywania działalności",
    "Województwo adresu lokalu, w którym jest prowadzona sprzedaż",
    "Powiat adresu lokalu, w którym jest prowadzona sprzedaż",
    "Gmina adresu lokalu, w którym jest prowadzona sprzedaż",
    "Miejscowość adresu lokalu, w którym jest prowadzona sprzedaż",
    "Ulica adresu lokalu, w którym jest prowadzona sprzedaż",
    "Numer nieruchomości adresu lokalu, w którym jest prowadzona sprzedaż",
    "Numer lokalu adresu lokalu, w którym jest prowadzona sprzedaż",
    "Kod pocztowy adresu lokalu, w którym jest prowadzona sprzedaż",
    "Dodatkowe lokalizacje, w których jest prowadzona sprzedaż",
    "Sposób kontaktu nabywcy z podmiotem obowiązanym",
    "Województwo lokalizacji przedsięwzięcia deweloperskiego lub zadania inwestycyjnego",
    "Powiat lokalizacji przedsięwzięcia deweloperskiego lub zadania inwestycyjnego",
    "Gmina lokalizacji przedsięwzięcia deweloperskiego lub zadania inwestycyjnego",
    "Miejscowość lokalizacji przedsięwzięcia deweloperskiego lub zadania inwestycyjnego",
    "Ulica lokalizacji przedsięwzięcia deweloperskiego lub zadania inwestycyjnego",
    "Numer nieruchomości lokalizacji przedsięwzięcia deweloperskiego lub zadania inwestycyjnego",
    "Kod pocztowy lokalizacji przedsięwzięcia deweloperskiego lub zadania inwestycyjnego",
    "Długość geograficzna punktu określającego lokalizację przestrzenną przedsięwzięcia deweloperskiego albo zadania inwestycyjnego",
    "Szerokość geograficzna punktu określającego lokalizację przestrzenną przedsięwzięcia deweloperskiego albo zadania inwestycyjnego",
    "Rodzaj nieruchomości",
    "Identyfikator lokalu mieszkalnego albo domu jednorodzinnego",
    "Cena 1 m² powierzchni użytkowej lokalu mieszkalnego albo domu jednorodzinnego",
    "Data i czas, od których obowiązuje cena 1 m² powierzchni użytkowej lokalu mieszkalnego albo domu jednorodzinnego",
    "Cena lokalu mieszkalnego albo domu jednorodzinnego lub ich części będących przedmiotem umowy",
    "Data i czas, od których obowiązuje cena lokalu mieszkalnego albo domu jednorodzinnego lub ich części",
    "Rodzaj pomieszczenia przynależnego, o którym mowa w art. 2 ust. 4 ustawy z dnia 24 czerwca 1994 r. o własności lokali",
    "Identyfikator pomieszczenia przynależnego, o którym mowa w art. 2 ust. 4 ustawy z dnia 24 czerwca 1994 r. o własności lokali",
    "Cena pomieszczenia przynależnego, o którym mowa w art. 2 ust. 4 ustawy z dnia 24 czerwca 1994 r. o własności lokali",
    "Data i czas, od których obowiązuje cena pomieszczenia przynależnego, o którym mowa w art. 2 ust. 4 ustawy z dnia 24 czerwca 1994 r. o własności lokali",
    "Identyfikator lokalu mieszkalnego albo domu jednorodzinnego przypisanego do pomieszczenia przynależnego",
    "Wyszczególnienie praw niezbędnych do korzystania z lokalu mieszkalnego albo domu jednorodzinnego",
    "Wartość praw niezbędnych do korzystania z lokalu mieszkalnego albo domu jednorodzinnego",
    "Data i czas, od których obowiązuje wartość praw niezbędnych do korzystania z lokalu mieszkalnego albo domu jednorodzinnego",
    "Identyfikator lokalu mieszkalnego albo domu jednorodzinnego przypisanego do prawa",
    "Wyszczególnienie rodzaju innego świadczenia pieniężnego, które nabywca jest zobowiązany spełnić na rzecz podmiotu obowiązanego w wykonaniu umowy przenoszącej własność",
    "Wartość innego świadczenia pieniężnego, które nabywca jest zobowiązany spełnić na rzecz podmiotu obowiązanego w wykonaniu umowy przenoszącej własność",
    "Data i czas, od których obowiązuje wartość innego świadczenia pieniężnego, które nabywca jest zobowiązany spełnić na rzecz podmiotu obowiązanego w wykonaniu umowy przenoszącej własność",
    "Identyfikator lokalu mieszkalnego albo domu jednorodzinnego przypisanego do innego świadczenia pieniężnego",
]


def validate_schema(df: pd.DataFrame) -> None:
    """Przerywa publikację, gdy kolumny nie odpowiadają oficjalnemu schematowi."""
    actual = list(df.columns)
    if actual == EXPECTED_COLUMNS:
        return

    missing = [column for column in EXPECTED_COLUMNS if column not in actual]
    extra = [column for column in actual if column not in EXPECTED_COLUMNS]
    details = []
    if missing:
        details.append(f"brakujące: {missing}")
    if extra:
        details.append(f"nadmiarowe: {extra}")
    if not missing and not extra:
        details.append("kolumny występują w niewłaściwej kolejności")
    raise ValueError("Nieprawidłowy schemat danych (" + "; ".join(details) + ").")
