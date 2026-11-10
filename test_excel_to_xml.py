import unittest
import xml.etree.ElementTree as ET

from excel_to_xml import DATASET_EXTIDENT, generuj_xml_dla_wszystkich_csv


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


if __name__ == "__main__":
    unittest.main()
