import unittest
import xml.etree.ElementTree as ET
import json
import tempfile
from pathlib import Path

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

    def test_json_jest_zamieniany_na_ten_sam_model_danych(self) -> None:
        row = {column: f"wartość-{index}" for index, column in enumerate(EXPECTED_COLUMNS)}
        with tempfile.TemporaryDirectory(dir=".") as directory:
            path = Path(directory) / "data.json"
            path.write_text(json.dumps({"data": [row]}, ensure_ascii=False), encoding="utf-8")
            frame = load_json(str(path))

        validate_schema(frame)
        self.assertEqual(len(frame), 1)
        self.assertEqual(list(frame.columns), EXPECTED_COLUMNS)


if __name__ == "__main__":
    unittest.main()
