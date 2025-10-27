#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konwerter Excel → XML dla portalu dane.gov.pl (Opcja A - Historia)
Kerim Sp. z o.o.
Wersja 3.0 - Skanuje wszystkie CSV w folderze i tworzy resource dla każdego
"""

import pandas as pd
from datetime import datetime
import hashlib
import xml.etree.ElementTree as ET
import os
import re
import glob

# ==================== KONFIGURACJA ====================
NAZWA_DEWELOPERA = "Kerim"
EXTIDENT_DATASET = "kerim_ceny_mieszkan_2025_dataset"
URL_BASE = "https://oskar-bednarek.github.io/ceny-mieszkan/"

XML_FILE = "kerim-ceny-mieszkan.xml"
MD5_FILE = "kerim-ceny-mieszkan.md5"

# ==================== FUNKCJE ====================

def wczytaj_excel(sciezka_excel):
    """Wczytuje dane z pliku Excel"""
    print(f"📂 Wczytuję dane z: {sciezka_excel}")
    df = pd.read_excel(sciezka_excel)
    print(f"✅ Wczytano {len(df)} lokali")
    return df

def znajdz_wszystkie_csv():
    """Znajduje wszystkie pliki CSV z cenami w folderze"""
    pattern = "Kerim-ceny-mieszkan-*.csv"
    pliki = glob.glob(pattern)
    
    # Wyciągnij daty z nazw plików
    daty = []
    for plik in pliki:
        # Szukaj daty w formacie YYYY-MM-DD
        match = re.search(r'(\d{4}-\d{2}-\d{2})', plik)
        if match:
            daty.append(match.group(1))
    
    daty.sort()  # Sortuj chronologicznie
    print(f"📊 Znaleziono {len(daty)} plików CSV:")
    for data in daty:
        print(f"   - {data}")
    
    return daty

def utworz_xml_root():
    """Tworzy główny element XML"""
    root = ET.Element('ns2:datasets')
    root.set('xmlns:ns2', 'urn:otwarte-dane:harvester:1.13')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    return root

def utworz_dataset(root, nazwa_dewelopera, rok):
    """Tworzy nowy dataset"""
    print(f"📄 Tworzę dataset: {EXTIDENT_DATASET}")
    dataset = ET.SubElement(root, 'dataset')
    dataset.set('status', 'published')
    
    extident = ET.SubElement(dataset, 'extIdent')
    extident.text = EXTIDENT_DATASET
    
    title = ET.SubElement(dataset, 'title')
    ET.SubElement(title, 'polish').text = f"Ceny ofertowe mieszkań dewelopera {nazwa_dewelopera} w {rok} r."
    ET.SubElement(title, 'english').text = f"Offer prices of apartments of developer {nazwa_dewelopera} in {rok}."
    
    description = ET.SubElement(dataset, 'description')
    ET.SubElement(description, 'polish').text = (
        f"Zbiór danych zawiera informacje o cenach ofertowych mieszkań dewelopera {nazwa_dewelopera} "
        f"udostępniane zgodnie z art. 19b. ust. 1 Ustawy z dnia 20 maja 2021 r. o ochronie praw nabywcy "
        f"lokalu mieszkalnego lub domu jednorodzinnego oraz Deweloperskim Funduszu Gwarancyjnym "
        f"(Dz. U. z 2024 r. poz. 695)."
    )
    ET.SubElement(description, 'english').text = (
        f"The dataset contains information on offer prices of apartments of the developer {nazwa_dewelopera} "
        f"made available in accordance with art. 19b. ust. 1 Ustawy z dnia 20 maja 2021 r. o ochronie praw "
        f"nabywcy lokalu mieszkalnego lub domu jednorodzinnego oraz Deweloperskim Funduszu Gwarancyjnym "
        f"(Dz. U. z 2024 r. poz. 695)."
    )
    
    ET.SubElement(dataset, 'updateFrequency').text = 'daily'
    ET.SubElement(dataset, 'hasDynamicData').text = 'false'
    ET.SubElement(dataset, 'hasHighValueData').text = 'true'
    ET.SubElement(dataset, 'hasHighValueDataFromEuropeanCommissionList').text = 'false'
    ET.SubElement(dataset, 'hasResearchData').text = 'false'
    
    categories = ET.SubElement(dataset, 'categories')
    ET.SubElement(categories, 'category').text = 'ECON'
    
    resources = ET.SubElement(dataset, 'resources')
    
    tags = ET.SubElement(dataset, 'tags')
    tag = ET.SubElement(tags, 'tag')
    tag.set('lang', 'pl')
    tag.text = 'Deweloper'
    
    return dataset, resources

def dodaj_resource(resources, data_publikacji):
    """Dodaje resource dla konkretnej daty"""
    
    extident_resource = f"kerim_dane_{data_publikacji.replace('-', '')}"[:36]
    
    print(f"➕ Dodaję resource: {extident_resource}")
    
    resource = ET.SubElement(resources, 'resource')
    resource.set('status', 'published')
    
    ET.SubElement(resource, 'extIdent').text = extident_resource
    
    url_csv = f"{URL_BASE}Kerim-ceny-mieszkan-{data_publikacji}.csv"
    ET.SubElement(resource, 'url').text = url_csv
    
    title = ET.SubElement(resource, 'title')
    ET.SubElement(title, 'polish').text = f"Ceny ofertowe mieszkań dewelopera {NAZWA_DEWELOPERA} {data_publikacji}"
    ET.SubElement(title, 'english').text = f"Offer prices for developer's apartments {NAZWA_DEWELOPERA} {data_publikacji}"
    
    description = ET.SubElement(resource, 'description')
    ET.SubElement(description, 'polish').text = (
        f"Dane dotyczące cen ofertowych mieszkań dewelopera {NAZWA_DEWELOPERA} "
        f"udostępnione {data_publikacji} zgodnie z art. 19b. ust. 1 Ustawy z dnia 20 maja 2021 r. "
        f"o ochronie praw nabywcy lokalu mieszkalnego lub domu jednorodzinnego oraz Deweloperskim "
        f"Funduszu Gwarancyjnym (Dz. U. z 2024 r. poz. 695)."
    )
    ET.SubElement(description, 'english').text = (
        f"Data on offer prices of apartments of the developer {NAZWA_DEWELOPERA} "
        f"made available {data_publikacji} in accordance with art. 19b. ust. 1 Ustawy z dnia 20 maja 2021 r. "
        f"o ochronie praw nabywcy lokalu mieszkalnego lub domu jednorodzinnego oraz Deweloperskim "
        f"Funduszu Gwarancyjnym (Dz. U. z 2024 r. poz. 695)."
    )
    
    ET.SubElement(resource, 'availability').text = 'local'
    ET.SubElement(resource, 'dataDate').text = data_publikacji
    
    special_signs = ET.SubElement(resource, 'specialSigns')
    ET.SubElement(special_signs, 'specialSign').text = 'X'
    
    ET.SubElement(resource, 'hasDynamicData').text = 'false'
    ET.SubElement(resource, 'hasHighValueData').text = 'true'
    ET.SubElement(resource, 'hasHighValueDataFromEuropeanCommissionList').text = 'false'
    ET.SubElement(resource, 'hasResearchData').text = 'false'
    ET.SubElement(resource, 'containsProtectedData').text = 'false'

def pretty_print_xml(element, level=0):
    """Formatuje XML bez pustych linii"""
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

def generuj_xml_dla_wszystkich_csv(daty_csv):
    """Generuje XML ze wszystkimi resources (po jednym dla każdego CSV)"""
    
    rok = datetime.now().year
    
    print(f"🔨 Generuję XML dla {len(daty_csv)} plików CSV")
    
    # Utwórz nowy XML od zera
    root = utworz_xml_root()
    
    # Utwórz dataset
    dataset, resources = utworz_dataset(root, NAZWA_DEWELOPERA, rok)
    
    # Dodaj resource dla każdego CSV
    for data in daty_csv:
        dodaj_resource(resources, data)
    
    # Formatuj XML (bez pustych linii)
    pretty_print_xml(root)
    
    # Konwertuj do stringa
    xml_str = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    
    return xml_str

def generuj_md5(xml_content):
    """Generuje hash MD5 dla pliku XML"""
    md5_hash = hashlib.md5(xml_content).hexdigest()
    return md5_hash

def zapisz_pliki(xml_content):
    """Zapisuje pliki XML i MD5"""
    
    # Zapisz XML
    with open(XML_FILE, 'wb') as f:
        f.write(xml_content)
    print(f"✅ Zapisano XML: {XML_FILE}")
    
    # Wygeneruj i zapisz MD5
    md5_hash = generuj_md5(xml_content)
    with open(MD5_FILE, 'w') as f:
        f.write(md5_hash)
    print(f"✅ Zapisano MD5: {MD5_FILE}")
    print(f"   Hash: {md5_hash}")
    
    return XML_FILE, MD5_FILE

def generuj_csv_dla_portalu(df, data_publikacji):
    """Generuje plik CSV dla dzisiejszej daty (jeśli nie istnieje)"""
    csv_path = f"Kerim-ceny-mieszkan-{data_publikacji}.csv"
    
    if os.path.exists(csv_path):
        print(f"ℹ️ CSV dla {data_publikacji} już istnieje: {csv_path}")
        return csv_path
    
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"✅ Utworzono nowy CSV: {csv_path}")
    return csv_path

# ==================== GŁÓWNA FUNKCJA ====================

def main():
    """Główna funkcja programu"""
    
    print("=" * 60)
    print("🏢 KERIM - Generator XML v3 (Skanuje wszystkie CSV)")
    print("=" * 60)
    
    excel_file = "Kerim_Dane_ceny_mieszkan.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"❌ Błąd: Nie znaleziono pliku {excel_file}")
        return
    
    try:
        # Wczytaj dane z Excela
        df = wczytaj_excel(excel_file)
        
        # Data dzisiejsza
        data_dzisiaj = datetime.now().strftime('%Y-%m-%d')
        
        # Wygeneruj CSV na dziś (jeśli nie istnieje)
        csv_dzisiaj = generuj_csv_dla_portalu(df, data_dzisiaj)
        
        # Znajdź wszystkie pliki CSV w folderze
        daty_csv = znajdz_wszystkie_csv()
        
        if not daty_csv:
            print("⚠️ Nie znaleziono żadnych plików CSV!")
            print("   Tworzę CSV dla dzisiejszej daty...")
            daty_csv = [data_dzisiaj]
        
        # Generuj XML dla WSZYSTKICH CSV
        xml_content = generuj_xml_dla_wszystkich_csv(daty_csv)
        
        # Zapisz pliki XML i MD5
        xml_path, md5_path = zapisz_pliki(xml_content)
        
        print("\n" + "=" * 60)
        print("✅ SUKCES! Pliki wygenerowane:")
        print(f"   📄 {xml_path} ({len(daty_csv)} resources)")
        print(f"   🔐 {md5_path}")
        print(f"   📊 {csv_dzisiaj}")
        print("=" * 60)
        print(f"\n💡 XML zawiera {len(daty_csv)} resources:")
        for data in daty_csv:
            print(f"   • {data}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Wystąpił błąd: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()