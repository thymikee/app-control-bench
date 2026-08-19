import os
import sys
import unittest


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import report_data


class HistoricalToolVersionTests(unittest.TestCase):
    def test_export_uses_captured_version_instead_of_next_run_pin(self):
        dataset = report_data.Dataset(
            tasks=[{"id": "element-01", "app": "element"}],
            tmap={"element-01": {"id": "element-01", "app": "element"}},
            models=["gpt_low"],
            rows={
                ("gpt_low", "agent-device", "element-01"): {
                    "meta": {"versions": {"tool": "0.17.6"}}
                }
            },
            annulled=frozenset(),
        )

        versions = report_data.observed_tool_versions(dataset)

        self.assertEqual(versions["agent-device"], "0.17.6")
        self.assertEqual(
            report_data.tool_entry("agent-device", versions)["version"], "0.17.6"
        )
        self.assertNotEqual(versions["agent-device"], report_data.TOOL_VERSIONS["agent-device"])

    def test_existing_versionless_rows_are_reported_as_unknown(self):
        dataset = report_data.Dataset(
            tasks=[{"id": "element-01", "app": "element"}],
            tmap={"element-01": {"id": "element-01", "app": "element"}},
            models=["gpt_low"],
            rows={("gpt_low", "agent-device", "element-01"): {"meta": {}}},
            annulled=frozenset(),
        )

        versions = report_data.observed_tool_versions(dataset)

        self.assertIsNone(versions["agent-device"])

    def test_tools_without_rows_use_the_next_run_pin(self):
        dataset = report_data.Dataset(
            tasks=[{"id": "element-01", "app": "element"}],
            tmap={"element-01": {"id": "element-01", "app": "element"}},
            models=["gpt_low"],
            rows={},
            annulled=frozenset(),
        )

        versions = report_data.observed_tool_versions(dataset)

        self.assertEqual(versions["agent-device"], "0.20.10")


if __name__ == "__main__":
    unittest.main()
