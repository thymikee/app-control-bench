import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import report_data


class ObservedToolVersionsTests(unittest.TestCase):
    def test_uses_recorded_versions_instead_of_current_pin(self):
        dataset = report_data.Dataset(
            tasks=[],
            tmap={},
            models=[],
            rows={
                ("gpt_low", "agent-device", "bsky-01"): {
                    "meta": {"versions": {"tool": "0.17.6"}}
                }
            },
            annulled=frozenset(),
        )

        self.assertEqual(report_data.observed_tool_versions(dataset)["agent-device"], "0.17.6")

    def test_discloses_mixed_versions_during_a_refresh(self):
        dataset = report_data.Dataset(
            tasks=[],
            tmap={},
            models=[],
            rows={
                ("gpt_low", "agent-device", "bsky-01"): {
                    "meta": {"versions": {"tool": "0.20.8"}}
                },
                ("gpt_high", "agent-device", "bsky-01"): {
                    "meta": {"versions": {"tool": "0.17.6"}}
                },
            },
            annulled=frozenset(),
        )

        self.assertEqual(
            report_data.observed_tool_versions(dataset)["agent-device"],
            "0.17.6 + 0.20.8",
        )


if __name__ == "__main__":
    unittest.main()
