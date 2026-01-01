#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konwerter Excel -> XML dla portalu dane.gov.pl (Opcja A - Historia)
Kerim Sp. z o.o.
Wersja 3.2 - Skanuje CSV z bieżącego roku, tworzy resource dla każdego
"""

import glob
import hashlib
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime

import pandas as pd

# ==================== KONFIGURACJA ====================
NAZWA_DEWELOPERA = "Kerim"
EXTIDENT_TEMPLATE = "kerim_ceny_mieszkan_{year}_dataset"
URL_BASE = "https://oskar-bednarek.github.io/ceny-mieszkan/"

CSV_ROOT_DIR = "csv"
CSV_FILENAME_TEMPLATE = "Kerim-ceny-mieszkan-{date}.csv"

XML_FILE = "kerim-ceny-mieszkan.xml"
MD5_FILE = "kerim-ceny-mieszkan.md5"
HISTORY_DIR = "history"


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


def utworz_dataset(root: ET.Element, nazwa_dewelopera: str, rok_datasetu: int) -> tuple[ET.Element, ET.Element]:
    """Tworzy dataset bez roku w tytule, ale z unikalnym extIdent na rok."""
    extident_dataset = EXTIDENT_TEMPLATE.format(year=rok_datasetu)
    print(f"-> Tworzę dataset: {extident_dataset}")

    dataset = ET.SubElement(root, "dataset")
    dataset.set("status", "published")

    extident = ET.SubElement(dataset, "extIdent")
    extident.text = extident_dataset

    title = ET.SubElement(dataset, "title")
    ET.SubElement(title, "polish").text = f"Ceny ofertowe mieszkań dewelopera {nazwa_dewelopera}"
    ET.SubElement(title, "english").text = f"Offer prices of apartments of developer {nazwa_dewelopera}"

    description = ET.SubElement(dataset, "description")
    ET.SubElement(description, "polish").text = (
        f"Zbiór danych zawiera informacje o cenach ofertowych mieszkań dewelopera {nazwa_dewelopera} "
        f"udostępniane zgodnie z art. 19b. ust. 1 Ustawy z dnia 20 maja 2021 r. o ochronie praw nabywcy "
        f"lokalu mieszkalnego lub domu jednorodzinnego oraz Deweloperskim Funduszu Gwarancyjnym "
        f"(Dz. U. z 2024 r. poz. 695)."
    )
    ET.SubElement(description, "english").text = (
        f"The dataset contains information on offer prices of apartments of the developer {nazwa_dewelopera} "
        f"made available in accordance with art. 19b. ust. 1 Ustawy z dnia 20 maja 2021 r. o ochronie praw "
        f"nabywcy lokalu mieszkalnego lub domu jednorodzinnego oraz Deweloperskim Funduszu Gwarancyjnym "
        f"(Dz. U. z 2024 r. poz. 695)."
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


def generuj_xml_dla_wszystkich_csv(daty_csv: list[str], rok_datasetu: int) -> bytes:
    """Generuje XML ze wszystkimi resources (po jednym dla każdego CSV)."""
    print(f"-> Generuję XML dla {len(daty_csv)} plików CSV")

    root = utworz_xml_root()
    dataset, resources = utworz_dataset(root, NAZWA_DEWELOPERA, rok_datasetu)

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


def zapisz_historyczny_xml(poprz_rok: int, wszystkie_daty: list[str]) -> tuple[str, str] | None:
    """Tworzy i zapisuje kopię XML/MD5 dla poprzedniego roku (jeśli są dane)."""
    daty_poprz = [d for d in wszystkie_daty if d.startswith(str(poprz_rok))]
    if not daty_poprz:
        return None

    os.makedirs(HISTORY_DIR, exist_ok=True)
    xml_content = generuj_xml_dla_wszystkich_csv(daty_poprz, poprz_rok)

    hist_xml_path = os.path.join(HISTORY_DIR, f"kerim-ceny-mieszkan-{poprz_rok}.xml")
    hist_md5_path = os.path.join(HISTORY_DIR, f"kerim-ceny-mieszkan-{poprz_rok}.md5")

    return zapisz_pliki(xml_content, hist_xml_path, hist_md5_path)


# ==================== GŁÓWNA FUNKCJA ====================
def main() -> None:
    """Główna funkcja programu."""
    print("=" * 60)
    print("KERIM - Generator XML v3.2 (Skanuje CSV z bieżącego roku)")
    print("=" * 60)

    excel_file = "Kerim_Dane_ceny_mieszkan.xlsx"

    if not os.path.exists(excel_file):
        print(f"!! Błąd: Nie znaleziono pliku {excel_file}")
        return

    try:
        df = wczytaj_excel(excel_file)
        data_dzisiaj = datetime.now().strftime("%Y-%m-%d")
        rok_biezacy = datetime.now().year
        csv_dzisiaj = generuj_csv_dla_portalu(df, data_dzisiaj)

        wszystkie_daty = znajdz_wszystkie_csv()
        daty_csv = [d for d in wszystkie_daty if d.startswith(str(rok_biezacy))]
        if not daty_csv:
            print("!! Nie znaleziono żadnych plików CSV!")
            print("   Tworzę CSV dla dzisiejszej daty...")
            daty_csv = [data_dzisiaj]

        xml_content = generuj_xml_dla_wszystkich_csv(daty_csv, rok_biezacy)
        xml_path, md5_path = zapisz_pliki(xml_content)

        hist_paths = zapisz_historyczny_xml(rok_biezacy - 1, wszystkie_daty)

        print("\n" + "=" * 60)
        print("SUKCES! Pliki wygenerowane:")
        print(f"   - {xml_path} ({len(daty_csv)} resources)")
        print(f"   - {md5_path}")
        print(f"   - {csv_dzisiaj}")
        if hist_paths:
            print(f"   - Archiwum poprzedniego roku: {hist_paths[0]} / {hist_paths[1]}")
        print("=" * 60)
        print(f"\nXML zawiera {len(daty_csv)} resources:")
        for data in daty_csv:
            print(f"   * {data}")
        print("=" * 60)

    except Exception as e:
        print(f"\n!! Wystąpił błąd: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
