#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konwerter Excel → XML dla portalu dane.gov.pl (Opcja A - Historia)
Kerim Sp. z o.o.
Wersja 2.0 - Akumulacja resources (każdy dzień = nowy resource)
"""

import pandas as pd
from datetime import datetime
import hashlib
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os

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

def wczytaj_istniejacy_xml():
    """Wczytuje istniejący XML jeśli istnieje"""
    if not os.path.exists(XML_FILE):
        print("📄 Brak istniejącego XML - tworzę nowy")
        return None
    
    try:
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
        print(f"✅ Wczytano istniejący XML")
        return root
    except Exception as e:
        print(f"⚠️ Błąd wczytywania XML: {e}")
        print("📄 Tworzę nowy XML")
        return None

def utworz_xml_root():
    """Tworzy główny element XML"""
    root = ET.Element('ns2:datasets')
    root.set('xmlns:ns2', 'urn:otwarte-dane:harvester:1.13')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    return root

def znajdz_lub_utworz_dataset(root, nazwa_dewelopera, rok):
    """Znajduje istniejący dataset lub tworzy nowy"""
    
    # Szukaj istniejącego datasetu
    ns = {'ns2': 'urn:otwarte-dane:harvester:1.13'}
    datasets = root.findall('.//ns2:dataset', ns)
    
    for dataset in datasets:
        extident = dataset.find('ns2:extIdent', ns)
        if extident is not None and extident.text == EXTIDENT_DATASET:
            print(f"✅ Znaleziono istniejący dataset: {EXTIDENT_DATASET}")
            resources = dataset.find('ns2:resources', ns)
            return dataset, resources
    
    # Jeśli nie znaleziono, utwórz nowy
    print(f"📄 Tworzę nowy dataset: {EXTIDENT_DATASET}")
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

def sprawdz_czy_resource_istnieje(resources, extident_szukany):
    """Sprawdza czy resource o danym extIdent już istnieje"""
    ns = {'ns2': 'urn:otwarte-dane:harvester:1.13'}
    
    for resource in resources.findall('ns2:resource', ns):
        extident = resource.find('ns2:extIdent', ns)
        if extident is not None and extident.text == extident_szukany:
            return True
    return False

def dodaj_resource(resources, data_publikacji):
    """Dodaje nowy resource - dane z konkretnego dnia"""
    
    extident_resource = f"kerim_dane_{data_publikacji.replace('-', '')}"[:36]
    
    # Sprawdź czy resource na ten dzień już istnieje
    if sprawdz_czy_resource_istnieje(resources, extident_resource):
        print(f"⚠️ Resource dla daty {data_publikacji} już istnieje - pomijam")
        return False
    
    print(f"➕ Dodaję nowy resource: {extident_resource}")
    
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
    
    return True

def policz_resources(resources):
    """Liczy ile resources jest w XML"""
    ns = {'ns2': 'urn:otwarte-dane:harvester:1.13'}
    return len(resources.findall('ns2:resource', ns))

def generuj_xml_z_akumulacja(df, data_publikacji=None):
    """Generuje XML z akumulacją resources (Opcja A)"""
    
    if data_publikacji is None:
        data_publikacji = datetime.now().strftime('%Y-%m-%d')
    
    rok = datetime.now().year
    
    print(f"🔨 Generuję XML z akumulacją dla daty: {data_publikacji}")
    
    # Wczytaj istniejący XML lub utwórz nowy
    root = wczytaj_istniejacy_xml()
    
    if root is None:
        root = utworz_xml_root()
    
    # Znajdź lub utwórz dataset
    dataset, resources = znajdz_lub_utworz_dataset(root, NAZWA_DEWELOPERA, rok)
    
    # Policz ile resources było przed
    liczba_przed = policz_resources(resources)
    print(f"📊 Resources przed: {liczba_przed}")
    
    # Dodaj nowy resource (jeśli nie istnieje)
    dodano = dodaj_resource(resources, data_publikacji)
    
    # Policz ile resources jest teraz
    liczba_po = policz_resources(resources)
    print(f"📊 Resources po: {liczba_po}")
    
    if dodano:
        print(f"✅ Dodano nowy resource dla {data_publikacji}")
    else:
        print(f"ℹ️ Resource dla {data_publikacji} już istniał")
    
    # Formatuj XML
    xml_str = minidom.parseString(ET.tostring(root, encoding='utf-8')).toprettyxml(indent="  ", encoding='utf-8')
    
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
    """Generuje plik CSV w formacie do przesłania na portal dane.gov.pl"""
    csv_path = f"Kerim-ceny-mieszkan-{data_publikacji}.csv"
    
    # Sprawdź czy CSV już istnieje
    if os.path.exists(csv_path):
        print(f"ℹ️ CSV dla {data_publikacji} już istnieje: {csv_path}")
        return csv_path
    
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"✅ Zapisano nowy CSV: {csv_path}")
    return csv_path

# ==================== GŁÓWNA FUNKCJA ====================

def main():
    """Główna funkcja programu"""
    
    print("=" * 60)
    print("🏢 KERIM - Generator XML (Opcja A - Historia)")
    print("=" * 60)
    
    excel_file = "Kerim_Dane_ceny_mieszkan.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"❌ Błąd: Nie znaleziono pliku {excel_file}")
        print(f"   Upewnij się, że plik Excel jest w tym samym folderze co skrypt.")
        return
    
    try:
        # Wczytaj dane
        df = wczytaj_excel(excel_file)
        
        # Data publikacji (dzisiejsza data)
        data_publikacji = datetime.now().strftime('%Y-%m-%d')
        
        # Generuj XML z akumulacją
        xml_content = generuj_xml_z_akumulacja(df, data_publikacji)
        
        # Zapisz pliki XML i MD5
        xml_path, md5_path = zapisz_pliki(xml_content)
        
        # Generuj CSV dla portalu (tylko jeśli nie istnieje)
        csv_path = generuj_csv_dla_portalu(df, data_publikacji)
        
        print("\n" + "=" * 60)
        print("✅ SUKCES! Pliki zaktualizowane:")
        print(f"   📄 {xml_path} (akumulacja resources)")
        print(f"   🔐 {md5_path}")
        print(f"   📊 {csv_path}")
        print("=" * 60)
        print("\n💡 Opcja A aktywna: Każdy dzień dodaje nowy resource")
        print("   Historia cen jest zachowana w zbiorze danych!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Wystąpił błąd: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()