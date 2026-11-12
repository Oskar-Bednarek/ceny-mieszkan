import unittest
import xml.etree.ElementTree as ET
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from excel_to_xml import DATASET_EXTIDENT, generuj_xml_dla_wszystkich_csv
from data_schema import EXPECTED_COLUMNS, validate_schema
from data_sources import load_json


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
        row = {column: f"wartość-{index}" for index, column in enumerate(EXPECTED_COLUMNS)}
        with tempfile.TemporaryDirectory(dir=".") as directory:
            path = Path(directory) / "data.json"
            path.write_text(json.dumps({"data": [row]}, ensure_ascii=False), encoding="utf-8")
            frame = load_json(str(path))

        validate_schema(frame)
        self.assertEqual(len(frame), 1)
        self.assertEqual(list(frame.columns), EXPECTED_COLUMNS)

    def test_odpowiedz_supabase_jest_rozpakowana_i_uporzadkowana(self) -> None:
        row = {column: f"wartość-{index}" for index, column in enumerate(reversed(EXPECTED_COLUMNS))}
        with tempfile.TemporaryDirectory(dir=".") as directory:
            path = Path(directory) / "supabase.json"
            path.write_text(json.dumps([{"rekord": row}], ensure_ascii=False), encoding="utf-8")
            frame = load_json(str(path))

        validate_schema(frame)
        self.assertEqual(frame.iloc[0][EXPECTED_COLUMNS[-1]], "wartość-0")

    def test_zdalne_zrodlo_dodaje_naglowki_supabase(self) -> None:
        row = {column: f"wartość-{index}" for index, column in enumerate(EXPECTED_COLUMNS)}
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


if __name__ == "__main__":
    unittest.main()
