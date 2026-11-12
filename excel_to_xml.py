#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konwerter Excel -> XML dla portalu dane.gov.pl
Kerim Sp. z o.o.
Wersja 4.0 - Jeden dataset obejmujący wszystkie historyczne i przyszłe CSV
"""

import glob
import hashlib
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from data_schema import validate_schema
from data_sources import load_source

# ==================== KONFIGURACJA ====================
NAZWA_DEWELOPERA = "Kerim"
# Zachowujemy dotychczasowy identyfikator, aby harvester aktualizował istniejący
# zbiór zamiast tworzyć nowy. Identyfikator pozostaje stały także w kolejnych latach.
DATASET_EXTIDENT = "kerim_ceny_mieszkan_2026_dataset"
URL_BASE = os.getenv("PUBLIC_BASE_URL", "https://oskar-bednarek.github.io/ceny-mieszkan/").rstrip("/") + "/"

EXCEL_FILE = "Kerim_Dane_ceny_mieszkan_nowa_struktura.xlsx"
SOURCE_TYPE = os.getenv("DATA_SOURCE_TYPE", "excel")
SOURCE_LOCATION = os.getenv("DATA_SOURCE_LOCATION", EXCEL_FILE)

CSV_ROOT_DIR = "csv"
CSV_FILENAME_TEMPLATE = "Kerim-ceny-mieszkan-{date}.csv"

XML_FILE = "kerim-ceny-mieszkan.xml"
MD5_FILE = "kerim-ceny-mieszkan.md5"
WARSAW_TIMEZONE = ZoneInfo("Europe/Warsaw")
NEW_LEGAL_BASIS_FROM = "2026-11-11"


# ==================== POMOCNICZE ====================
def csv_storage_dir(data_publikacji: str) -> str:
    """Zwraca katalog przechowywania CSV dla konkretnego roku."""
    year = data_publikacji.split("-")[0]
    return os.path.join(CSV_ROOT_DIR, year)


def csv_filename(data_publikacji: str) -> str:
    return CSV_FILENAME_TEMPLATE.format(date=data_publikacji)


def csv_path(data_publikacji: str) -> str:
    """Pełna ścieżka do lokalnego pliku CSV."""
    return os.path.join(csv_storage_dir(data_publikacji), csv_filename(data_publikacji))


def csv_url(data_publikacji: str) -> str:
    """Pełny URL pliku CSV publikowanego na GitHub Pages."""
    year = data_publikacji.split("-")[0]
    return f"{URL_BASE}{CSV_ROOT_DIR}/{year}/{csv_filename(data_publikacji)}"


# ==================== FUNKCJE ====================
def wczytaj_excel(sciezka_excel: str) -> pd.DataFrame:
    """Wczytuje dane z pliku Excel."""
    print(f"-> Wczytuję dane z: {sciezka_excel}")
    df = pd.read_excel(sciezka_excel)
    print(f"-> Wczytano {len(df)} lokali")
    return df


def wczytaj_dane(source_type: str = SOURCE_TYPE, location: str = SOURCE_LOCATION) -> pd.DataFrame:
    """Wczytuje i waliduje dane z Excela albo JSON-u (lokalnego lub HTTPS)."""
    source_label = "skonfigurowany endpoint HTTPS" if location.startswith("https://") else location
    print(f"-> Wczytuję źródło {source_type}: {source_label}")
    df = load_source(source_type, location)
    validate_schema(df)
    print(f"-> Wczytano {len(df)} lokali; schemat 48 kolumn jest poprawny")
    return df


def znajdz_wszystkie_csv() -> list[str]:
    """Znajduje wszystkie pliki CSV z cenami w folderze (rekurencyjnie)."""
    patterns = [
        os.path.join(CSV_ROOT_DIR, "*", CSV_FILENAME_TEMPLATE.format(date="*")),
        CSV_FILENAME_TEMPLATE.format(date="*"),  # wsparcie dla starych lokalizacji
    ]

    pliki: list[str] = []
    for pattern in patterns:
        pliki.extend(glob.glob(pattern))

    daty: list[str] = []
    for plik in pliki:
        match = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(plik))
        if match:
            daty.append(match.group(1))

    daty = sorted(set(daty))
    print(f"-> Znaleziono {len(daty)} plików CSV:")
    for data in daty:
        print(f"   - {data}")

    return daty


def utworz_xml_root() -> ET.Element:
    """Tworzy główny element XML."""
    root = ET.Element("ns2:datasets")
    root.set("xmlns:ns2", "urn:otwarte-dane:harvester:1.13")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    return root


def utworz_dataset(
    root: ET.Element, nazwa_dewelopera: str
) -> tuple[ET.Element, ET.Element]:
    """Tworzy jeden stały dataset zawierający zasoby ze wszystkich lat."""
    print(f"-> Tworzę dataset: {DATASET_EXTIDENT}")

    dataset = ET.SubElement(root, "dataset")
    dataset.set("status", "published")

    extident = ET.SubElement(dataset, "extIdent")
    extident.text = DATASET_EXTIDENT

    title = ET.SubElement(dataset, "title")
    ET.SubElement(title, "polish").text = f"Ceny ofertowe mieszkań dewelopera {nazwa_dewelopera}"
    ET.SubElement(title, "english").text = f"Offer prices of apartments of developer {nazwa_dewelopera}"

    description = ET.SubElement(dataset, "description")
    ET.SubElement(description, "polish").text = (
        f"Zbiór danych zawiera historyczne i bieżące informacje o cenach ofertowych mieszkań "
        f"dewelopera {nazwa_dewelopera} "
        f"udostępniane zgodnie z art. 19b ust. 1 ustawy z dnia 20 maja 2021 r. o ochronie praw nabywcy "
        f"lokalu mieszkalnego lub domu jednorodzinnego oraz Deweloperskim Funduszu Gwarancyjnym "
        f"(Dz. U. z 2026 r. poz. 880 i 1077). Zasoby przekazywane od 11 listopada 2026 r. "
        f"mają strukturę określoną w rozporządzeniu "
        f"Ministra Cyfryzacji z dnia 10 listopada 2026 r. w sprawie struktury danych zawartych "
        f"w informacjach dotyczących sprzedaży lokali mieszkalnych i domów jednorodzinnych "
        f"(Dz. U. z 2026 r. poz. 1489)."
    )
    ET.SubElement(description, "english").text = (
        f"The dataset contains historical and current information on offer prices of apartments "
        f"of the developer {nazwa_dewelopera} "
        f"made available pursuant to Article 19b(1) of the Act of 20 May 2021 on the protection "
        f"of the rights of buyers of residential premises or single-family houses and the Developer "
        f"Guarantee Fund (Journal of Laws of 2026, items 880 and 1077). Resources provided from "
        f"11 November 2026 follow the structure "
        f"specified in the Regulation of the Minister of Digital Affairs of 10 November 2026 "
        f"(Journal of Laws of 2026, item 1489)."
    )

    ET.SubElement(dataset, "updateFrequency").text = "daily"
    ET.SubElement(dataset, "hasDynamicData").text = "false"
    ET.SubElement(dataset, "hasHighValueData").text = "true"
    ET.SubElement(dataset, "hasHighValueDataFromEuropeanCommissionList").text = "false"
    ET.SubElement(dataset, "hasResearchData").text = "false"

    categories = ET.SubElement(dataset, "categories")
    ET.SubElement(categories, "category").text = "ECON"

    resources = ET.SubElement(dataset, "resources")

    tags = ET.SubElement(dataset, "tags")
    tag = ET.SubElement(tags, "tag")
    tag.set("lang", "pl")
    tag.text = "Deweloper"

    return dataset, resources


def dodaj_resource(resources: ET.Element, data_publikacji: str) -> None:
    """Dodaje resource dla konkretnej daty."""
    extident_resource = f"kerim_dane_{data_publikacji.replace('-', '')}"[:36]
    print(f"-> Dodaję resource: {extident_resource}")

    resource = ET.SubElement(resources, "resource")
    resource.set("status", "published")

    ET.SubElement(resource, "extIdent").text = extident_resource
    ET.SubElement(resource, "url").text = csv_url(data_publikacji)

    title = ET.SubElement(resource, "title")
    ET.SubElement(title, "polish").text = f"Ceny ofertowe mieszkań dewelopera {NAZWA_DEWELOPERA} {data_publikacji}"
    ET.SubElement(title, "english").text = f"Offer prices for developer's apartments {NAZWA_DEWELOPERA} {data_publikacji}"

    description = ET.SubElement(resource, "description")
    if data_publikacji >= NEW_LEGAL_BASIS_FROM:
        ET.SubElement(description, "polish").text = (
            f"Dane dotyczące cen ofertowych mieszkań dewelopera {NAZWA_DEWELOPERA} według stanu "
            f"na dzień {data_publikacji}, przekazane zgodnie z art. 19b ust. 1 ustawy z dnia "
            f"20 maja 2021 r. o ochronie praw nabywcy lokalu mieszkalnego lub domu jednorodzinnego "
            f"oraz Deweloperskim Funduszu Gwarancyjnym (Dz. U. z 2026 r. poz. 880 i 1077). "
            f"Struktura danych jest zgodna z rozporządzeniem Ministra Cyfryzacji z dnia "
            f"10 listopada 2026 r. w sprawie struktury danych zawartych w informacjach dotyczących "
            f"sprzedaży lokali mieszkalnych i domów jednorodzinnych (Dz. U. z 2026 r. poz. 1489)."
        )
        ET.SubElement(description, "english").text = (
            f"Data on offer prices of apartments of the developer {NAZWA_DEWELOPERA}, current as of "
            f"{data_publikacji}, provided pursuant to Article 19b(1) of the Act of 20 May 2021 on the "
            f"protection of the rights of buyers of residential premises or single-family houses and "
            f"the Developer Guarantee Fund (Journal of Laws of 2026, items 880 and 1077). The data "
            f"follows the structure specified in the Regulation of the Minister of Digital Affairs "
            f"of 10 November 2026 (Journal of Laws of 2026, item 1489)."
        )
    else:
        ET.SubElement(description, "polish").text = (
            f"Dane dotyczące cen ofertowych mieszkań dewelopera {NAZWA_DEWELOPERA} "
            f"udostępnione {data_publikacji} zgodnie z art. 19b. ust. 1 Ustawy z dnia 20 maja 2021 r. "
            f"o ochronie praw nabywcy lokalu mieszkalnego lub domu jednorodzinnego oraz Deweloperskim "
            f"Funduszu Gwarancyjnym (Dz. U. z 2024 r. poz. 695)."
        )
        ET.SubElement(description, "english").text = (
            f"Data on offer prices of apartments of the developer {NAZWA_DEWELOPERA} "
            f"made available {data_publikacji} in accordance with art. 19b. ust. 1 Ustawy z dnia 20 maja 2021 r. "
            f"o ochronie praw nabywcy lokalu mieszkalnego lub domu jednorodzinnego oraz Deweloperskim "
            f"Funduszu Gwarancyjnym (Dz. U. z 2024 r. poz. 695)."
        )

    ET.SubElement(resource, "availability").text = "local"
    ET.SubElement(resource, "dataDate").text = data_publikacji

    special_signs = ET.SubElement(resource, "specialSigns")
    ET.SubElement(special_signs, "specialSign").text = "X"

    ET.SubElement(resource, "hasDynamicData").text = "false"
    ET.SubElement(resource, "hasHighValueData").text = "true"
    ET.SubElement(resource, "hasHighValueDataFromEuropeanCommissionList").text = "false"
    ET.SubElement(resource, "hasResearchData").text = "false"
    ET.SubElement(resource, "containsProtectedData").text = "false"


def pretty_print_xml(element: ET.Element, level: int = 0) -> None:
    """Formatuje XML bez pustych linii."""
    indent = "  "
    i = "\n" + level * indent
    if len(element):
        if not element.text or not element.text.strip():
            element.text = i + indent
        if not element.tail or not element.tail.strip():
            element.tail = i
        for child in element:
            pretty_print_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    else:
        if level and (not element.tail or not element.tail.strip()):
            element.tail = i


def generuj_xml_dla_wszystkich_csv(daty_csv: list[str]) -> bytes:
    """Generuje jeden XML i jeden dataset ze wszystkimi zasobami CSV."""
    daty_csv = sorted(set(daty_csv))
    print(f"-> Generuję jeden dataset dla {len(daty_csv)} plików CSV")

    root = utworz_xml_root()
    _, resources = utworz_dataset(root, NAZWA_DEWELOPERA)
    for data in daty_csv:
        dodaj_resource(resources, data)

    pretty_print_xml(root)
    xml_str = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return xml_str


def generuj_md5(xml_content: bytes) -> str:
    """Generuje hash MD5 dla pliku XML."""
    return hashlib.md5(xml_content).hexdigest()


def zapisz_pliki(xml_content: bytes, xml_path: str = XML_FILE, md5_path: str = MD5_FILE) -> tuple[str, str]:
    """Zapisuje pliki XML i MD5 w podanych ścieżkach."""
    with open(xml_path, "wb") as f:
        f.write(xml_content)
    print(f"-> Zapisano XML: {xml_path}")

    md5_hash = generuj_md5(xml_content)
    with open(md5_path, "w", encoding="utf-8") as f:
        f.write(md5_hash)
    print(f"-> Zapisano MD5: {md5_path}")
    print(f"   Hash: {md5_hash}")

    return xml_path, md5_path


def generuj_csv_dla_portalu(df: pd.DataFrame, data_publikacji: str) -> str:
    """Generuje plik CSV dla dzisiejszej daty (jeśli nie istnieje)."""
    dest_dir = csv_storage_dir(data_publikacji)
    os.makedirs(dest_dir, exist_ok=True)

    csv_destination = csv_path(data_publikacji)
    if os.path.exists(csv_destination):
        print(f"-> CSV dla {data_publikacji} już istnieje: {csv_destination}")
        return csv_destination

    df.to_csv(csv_destination, index=False, encoding="utf-8")
    print(f"-> Utworzono nowy CSV: {csv_destination}")
    return csv_destination


# ==================== GŁÓWNA FUNKCJA ====================
def main() -> None:
    """Główna funkcja programu."""
    print("=" * 60)
    print("KERIM - Generator XML v4.0 (Jeden dataset, pełna historia)")
    print("=" * 60)

    if SOURCE_TYPE == "excel" and not os.path.exists(SOURCE_LOCATION):
        raise SystemExit(f"!! Błąd: Nie znaleziono pliku {SOURCE_LOCATION}")

    try:
        df = wczytaj_dane()
        # Runner GitHuba pracuje domyślnie w UTC. Data zasobu ma oznaczać
        # bieżący dzień w Polsce, również przy uruchomieniu blisko północy.
        data_dzisiaj = datetime.now(WARSAW_TIMEZONE).strftime("%Y-%m-%d")
        csv_dzisiaj = generuj_csv_dla_portalu(df, data_dzisiaj)

        wszystkie_daty = znajdz_wszystkie_csv()
        if not wszystkie_daty:
            print("!! Nie znaleziono żadnych plików CSV!")
            print("   Tworzę CSV dla dzisiejszej daty...")
            wszystkie_daty = [data_dzisiaj]

        xml_content = generuj_xml_dla_wszystkich_csv(wszystkie_daty)
        xml_path, md5_path = zapisz_pliki(xml_content)

        print("\n" + "=" * 60)
        print("SUKCES! Pliki wygenerowane:")
        print(f"   - {xml_path} ({len(wszystkie_daty)} resources)")
        print(f"   - {md5_path}")
        print(f"   - {csv_dzisiaj}")
        print("=" * 60)
        print(f"\nXML zawiera {len(wszystkie_daty)} resources:")
        for data in wszystkie_daty:
            print(f"   * {data}")
        print("=" * 60)

    except Exception as e:
        print(f"\n!! Wystąpił błąd: {str(e)}")
        import traceback

        traceback.print_exc()
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
