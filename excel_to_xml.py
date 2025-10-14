#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konwerter Excel → XML dla portalu dane.gov.pl
Kerim Sp. z o.o.
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
URL_BASE = "https://TWOJA-NAZWA.github.io/ceny-mieszkan/"  # Wypełnimy później

# ==================== FUNKCJE ====================

def wczytaj_excel(sciezka_excel):
    """Wczytuje dane z pliku Excel"""
    print(f"📂 Wczytuję dane z: {sciezka_excel}")
    df = pd.read_excel(sciezka_excel)
    print(f"✅ Wczytano {len(df)} lokali")
    return df

def utworz_xml_root():
    """Tworzy główny element XML"""
    root = ET.Element('ns2:datasets')
    root.set('xmlns:ns2', 'urn:otwarte-dane:harvester:1.13')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    return root

def dodaj_dataset(root, nazwa_dewelopera, rok):
    """Dodaje główny element dataset (zbiór danych)"""
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
    """Dodaje zasób (resource) - dane z konkretnego dnia"""
    
    extident_resource = f"kerim_dane_{data_publikacji.replace('-', '')}"[:36]
    
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

def generuj_xml(df, data_publikacji=None):
    """Generuje plik XML z danymi z DataFrame"""
    
    if data_publikacji is None:
        data_publikacji = datetime.now().strftime('%Y-%m-%d')
    
    rok = datetime.now().year
    
    print(f"🔨 Generuję XML dla daty: {data_publikacji}")
    
    root = utworz_xml_root()
    dataset, resources = dodaj_dataset(root, NAZWA_DEWELOPERA, rok)
    dodaj_resource(resources, data_publikacji)
    
    xml_str = minidom.parseString(ET.tostring(root, encoding='utf-8')).toprettyxml(indent="  ", encoding='utf-8')
    
    return xml_str

def generuj_md5(xml_content):
    """Generuje hash MD5 dla pliku XML"""
    md5_hash = hashlib.md5(xml_content).hexdigest()
    return md5_hash

def zapisz_pliki(xml_content, nazwa_bazowa="kerim-ceny-mieszkan"):
    """Zapisuje pliki XML i MD5"""
    
    xml_path = f"{nazwa_bazowa}.xml"
    with open(xml_path, 'wb') as f:
        f.write(xml_content)
    print(f"✅ Zapisano XML: {xml_path}")
    
    md5_hash = generuj_md5(xml_content)
    md5_path = f"{nazwa_bazowa}.md5"
    with open(md5_path, 'w') as f:
        f.write(md5_hash)
    print(f"✅ Zapisano MD5: {md5_path}")
    print(f"   Hash: {md5_hash}")
    
    return xml_path, md5_path

def generuj_csv_dla_portalu(df, data_publikacji):
    """Generuje plik CSV w formacie do przesłania na portal dane.gov.pl"""
    csv_path = f"Kerim-ceny-mieszkan-{data_publikacji}.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"✅ Zapisano CSV: {csv_path}")
    return csv_path

def main():
    """Główna funkcja programu"""
    
    print("=" * 60)
    print("🏢 KERIM - Generator XML dla portalu dane.gov.pl")
    print("=" * 60)
    
    excel_file = "Kerim_Dane_ceny_mieszkan.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"❌ Błąd: Nie znaleziono pliku {excel_file}")
        print(f"   Upewnij się, że plik Excel jest w tym samym folderze co skrypt.")
        return
    
    try:
        df = wczytaj_excel(excel_file)
        data_publikacji = datetime.now().strftime('%Y-%m-%d')
        xml_content = generuj_xml(df, data_publikacji)
        xml_path, md5_path = zapisz_pliki(xml_content)
        csv_path = generuj_csv_dla_portalu(df, data_publikacji)
        
        print("\n" + "=" * 60)
        print("✅ SUKCES! Pliki wygenerowane:")
        print(f"   📄 {xml_path}")
        print(f"   🔐 {md5_path}")
        print(f"   📊 {csv_path}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Wystąpił błąd: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()