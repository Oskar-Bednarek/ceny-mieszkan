import unittest
import xml.etree.ElementTree as ET
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from excel_to_xml import DATASET_EXTIDENT, generuj_xml_dla_wszystkich_csv
from data_schema import EXPECTED_COLUMNS, validate_schema
from data_sources import MONEY_COLUMNS, load_json


def with_valid_money(row: dict) -> dict:
    """Nadaje technicznie poprawne kwoty rekordom używanym w testach schematu."""
    for column in MONEY_COLUMNS:
        if column in row and row[column] != "X":
            row[column] = 100
    return row


class GeneratorXmlTest(unittest.TestCase):
    def test_wszystkie_lata_trafiaja_do_jednego_datasetu(self) -> None:
        xml_content = generuj_xml_dla_wszystkich_csv(
            ["2026-01-02", "2025-12-31", "2026-01-01", "2026-01-01"]
        )
        root = ET.fromstring(xml_content)
        datasets = root.findall("dataset")

        self.assertEqual(len(datasets), 1)
        dataset = datasets[0]
        self.assertEqual(dataset.findtext("extIdent"), DATASET_EXTIDENT)
        self.assertEqual(dataset.findtext("updateFrequency"), "daily")
        self.assertEqual(
            [r.findtext("dataDate") for r in dataset.findall("./resources/resource")],
            ["2025-12-31", "2026-01-01", "2026-01-02"],
        )
        self.assertEqual(
            dataset.findtext("./title/polish"),
            "Ceny ofertowe mieszkań dewelopera Kerim",
        )

    def test_walidacja_odrzuca_zmieniona_strukture(self) -> None:
        with self.assertRaisesRegex(ValueError, "brakujące"):
            validate_schema(pd.DataFrame(columns=EXPECTED_COLUMNS[:-1]))

    def test_nowa_podstawa_prawna_dotyczy_zasobow_od_11_listopada(self) -> None:
        xml_content = generuj_xml_dla_wszystkich_csv(["2026-11-10", "2026-11-11"])
        root = ET.fromstring(xml_content)
        resources = root.findall("./dataset/resources/resource")
        descriptions = {
            resource.findtext("dataDate"): resource.findtext("./description/polish")
            for resource in resources
        }

        self.assertIn("Dz. U. z 2024 r. poz. 695", descriptions["2026-11-10"])
        self.assertNotIn("poz. 1489", descriptions["2026-11-10"])
        self.assertIn("Dz. U. z 2026 r. poz. 880 i 1077", descriptions["2026-11-11"])
        self.assertIn("poz. 1489", descriptions["2026-11-11"])

    def test_json_jest_zamieniany_na_ten_sam_model_danych(self) -> None:
        row = with_valid_money(
            {column: f"wartość-{index}" for index, column in enumerate(EXPECTED_COLUMNS)}
        )
        with tempfile.TemporaryDirectory(dir=".") as directory:
            path = Path(directory) / "data.json"
            path.write_text(json.dumps({"data": [row]}, ensure_ascii=False), encoding="utf-8")
            frame = load_json(str(path))

        validate_schema(frame)
        self.assertEqual(len(frame), 1)
        self.assertEqual(list(frame.columns), EXPECTED_COLUMNS)

    def test_odpowiedz_supabase_jest_rozpakowana_i_uporzadkowana(self) -> None:
        row = with_valid_money(
            {column: f"wartość-{index}" for index, column in enumerate(reversed(EXPECTED_COLUMNS))}
        )
        with tempfile.TemporaryDirectory(dir=".") as directory:
            path = Path(directory) / "supabase.json"
            path.write_text(json.dumps([{"rekord": row}], ensure_ascii=False), encoding="utf-8")
            frame = load_json(str(path))

        validate_schema(frame)
        self.assertEqual(frame.iloc[0][EXPECTED_COLUMNS[-1]], "wartość-0")

    def test_zdalne_zrodlo_dodaje_naglowki_supabase(self) -> None:
        row = with_valid_money(
            {column: f"wartość-{index}" for index, column in enumerate(EXPECTED_COLUMNS)}
        )
        response = tempfile.SpooledTemporaryFile()
        response.write(json.dumps([{"rekord": row}], ensure_ascii=False).encode("utf-8"))
        response.seek(0)

        with (
            patch.dict("os.environ", {"DATA_SOURCE_API_KEY": "test-publishable-key"}),
            patch("data_sources.urlopen", return_value=response) as mocked_urlopen,
        ):
            frame = load_json("https://example.supabase.co/rest/v1/oferty?select=rekord")

        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Apikey"), "test-publishable-key")
        self.assertEqual(request.get_header("Accept-profile"), "dane_gov_api")
        validate_schema(frame)

    def test_pusty_json_daje_csv_z_pelnym_schematem(self) -> None:
        with tempfile.TemporaryDirectory(dir=".") as directory:
            path = Path(directory) / "data.json"
            path.write_text('{"data": []}', encoding="utf-8")
            frame = load_json(str(path))

        validate_schema(frame)
        self.assertTrue(frame.empty)
        self.assertEqual(list(frame.columns), EXPECTED_COLUMNS)

    def test_model_aplikacji_jest_splaszczany_do_oficjalnego_schematu(self) -> None:
        row = with_valid_money(
            {column: f"wartość-{index}" for index, column in enumerate(EXPECTED_COLUMNS[:35])}
        )
        row["Numer identyfikacji podatkowej (NIP)"] = row.pop(
            "Numer Identyfikacji Podatkowej (NIP)"
        )
        row["Pomieszczenia przynależne"] = [
            {column: f"pomieszczenie-{index}" for index, column in enumerate(EXPECTED_COLUMNS[35:40])}
        ]
        row["Pomieszczenia przynależne"][0][EXPECTED_COLUMNS[37]] = 100
        row["Prawa niezbędne do korzystania"] = []
        row["Inne świadczenia pieniężne"] = []

        with tempfile.TemporaryDirectory(dir=".") as directory:
            path = Path(directory) / "app.json"
            path.write_text(json.dumps([{"rekord": row}], ensure_ascii=False), encoding="utf-8")
            frame = load_json(str(path))

        validate_schema(frame)
        self.assertEqual(frame.iloc[0][EXPECTED_COLUMNS[35]], "pomieszczenie-0")
        self.assertEqual(frame.iloc[0][EXPECTED_COLUMNS[40]], "X")

    def test_nieznane_pola_sekcji_sa_odrzucane(self) -> None:
        row = with_valid_money({column: "wartość" for column in EXPECTED_COLUMNS[:35]})
        row["Pomieszczenia przynależne"] = []
        row["Prawa niezbędne do korzystania"] = [{"nazwa": "Udział w drodze"}]
        row["Inne świadczenia pieniężne"] = []

        with tempfile.TemporaryDirectory(dir=".") as directory:
            path = Path(directory) / "invalid-section.json"
            path.write_text(json.dumps([{"rekord": row}], ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Nieprawidłowa sekcja"):
                load_json(str(path))

    def test_skrocony_identyfikator_lokalu_jest_mapowany_w_kontekscie_sekcji(self) -> None:
        row = with_valid_money({column: "wartość" for column in EXPECTED_COLUMNS[:35]})
        right = {column: "wartość" for column in EXPECTED_COLUMNS[40:44]}
        right[EXPECTED_COLUMNS[41]] = 100
        right["Identyfikator lokalu mieszkalnego albo domu jednorodzinnego"] = right.pop(
            EXPECTED_COLUMNS[43]
        )
        row["Pomieszczenia przynależne"] = []
        row["Prawa niezbędne do korzystania"] = [right]
        row["Inne świadczenia pieniężne"] = []

        with tempfile.TemporaryDirectory(dir=".") as directory:
            path = Path(directory) / "section-alias.json"
            path.write_text(json.dumps([{"rekord": row}], ensure_ascii=False), encoding="utf-8")
            frame = load_json(str(path))

        validate_schema(frame)
        self.assertEqual(frame.iloc[0][EXPECTED_COLUMNS[43]], "wartość")

    def test_plaski_model_uzupelnia_identyfikatory_lokalu_dla_sekcji(self) -> None:
        row = {column: "X" for column in EXPECTED_COLUMNS}
        for column in EXPECTED_COLUMNS[:35]:
            row[column] = "wartość"
        with_valid_money(row)
        row[EXPECTED_COLUMNS[30]] = "L-1"
        row[EXPECTED_COLUMNS[40]] = "Udział w działce drogowej"
        row[EXPECTED_COLUMNS[41]] = 5000
        row[EXPECTED_COLUMNS[42]] = "2026-09-24 00:00:00"
        for column in (EXPECTED_COLUMNS[39], EXPECTED_COLUMNS[43], EXPECTED_COLUMNS[47]):
            row.pop(column)

        with tempfile.TemporaryDirectory(dir=".") as directory:
            path = Path(directory) / "flat.json"
            path.write_text(json.dumps([{"rekord": row}], ensure_ascii=False), encoding="utf-8")
            frame = load_json(str(path))

        validate_schema(frame)
        self.assertEqual(frame.iloc[0][EXPECTED_COLUMNS[39]], "X")
        self.assertEqual(frame.iloc[0][EXPECTED_COLUMNS[43]], "L-1")
        self.assertEqual(frame.iloc[0][EXPECTED_COLUMNS[47]], "X")

    def test_puste_wartosci_sa_zamieniane_na_x_a_kwoty_formatowane(self) -> None:
        row = {column: "wartość" for column in EXPECTED_COLUMNS}
        row[EXPECTED_COLUMNS[18]] = None
        row[EXPECTED_COLUMNS[35]] = ""
        row[EXPECTED_COLUMNS[31]] = 10815.7
        row[EXPECTED_COLUMNS[33]] = 1790000
        row[EXPECTED_COLUMNS[37]] = None
        row[EXPECTED_COLUMNS[41]] = 0
        row[EXPECTED_COLUMNS[45]] = "5000.5"

        with tempfile.TemporaryDirectory(dir=".") as directory:
            path = Path(directory) / "values.json"
            path.write_text(json.dumps([{"rekord": row}], ensure_ascii=False), encoding="utf-8")
            frame = load_json(str(path))

        self.assertEqual(frame.iloc[0][EXPECTED_COLUMNS[18]], "X")
        self.assertEqual(frame.iloc[0][EXPECTED_COLUMNS[35]], "X")
        self.assertEqual(frame.iloc[0][EXPECTED_COLUMNS[31]], "10815.70")
        self.assertEqual(frame.iloc[0][EXPECTED_COLUMNS[33]], "1790000.00")
        self.assertEqual(frame.iloc[0][EXPECTED_COLUMNS[37]], "X")
        self.assertEqual(frame.iloc[0][EXPECTED_COLUMNS[41]], "0.00")
        self.assertEqual(frame.iloc[0][EXPECTED_COLUMNS[45]], "5000.50")

    def test_brakujace_plaskie_pola_sa_uzupelniane_znakiem_x(self) -> None:
        row = with_valid_money({column: "wartość" for column in EXPECTED_COLUMNS[:35]})

        with tempfile.TemporaryDirectory(dir=".") as directory:
            path = Path(directory) / "missing-flat-fields.json"
            path.write_text(json.dumps([{"rekord": row}], ensure_ascii=False), encoding="utf-8")
            frame = load_json(str(path))

        validate_schema(frame)
        self.assertTrue(all(frame.iloc[0][column] == "X" for column in EXPECTED_COLUMNS[35:]))

    def test_wiecej_niz_jeden_element_sekcji_jest_odrzucany(self) -> None:
        row = {column: "wartość" for column in EXPECTED_COLUMNS[:35]}
        item = {column: "wartość" for column in EXPECTED_COLUMNS[35:40]}
        row["Pomieszczenia przynależne"] = [item, item]
        row["Prawa niezbędne do korzystania"] = []
        row["Inne świadczenia pieniężne"] = []

        with tempfile.TemporaryDirectory(dir=".") as directory:
            path = Path(directory) / "too-many-items.json"
            path.write_text(json.dumps([{"rekord": row}], ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "najwyżej jeden element"):
                load_json(str(path))

    def test_pusty_obiekt_sekcji_jest_odrzucany(self) -> None:
        row = {column: "wartość" for column in EXPECTED_COLUMNS[:35]}
        row["Pomieszczenia przynależne"] = [{}]
        row["Prawa niezbędne do korzystania"] = []
        row["Inne świadczenia pieniężne"] = []

        with tempfile.TemporaryDirectory(dir=".") as directory:
            path = Path(directory) / "empty-item.json"
            path.write_text(json.dumps([{"rekord": row}], ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "brakujące pola"):
                load_json(str(path))


if __name__ == "__main__":
    unittest.main()
