import unittest
from tracker import analytics, grade_key, normalize, existing_records

class TrackerTests(unittest.TestCase):
    def test_record_fingerprint_is_stable(self):
        a = normalize({"board": "kilter", "climb_name": "Test", "date": "2026-01-01", "is_ascent": "True"})
        b = normalize({"board": "kilter", "climb_name": "Test", "date": "2026-01-01", "is_ascent": True})
        self.assertEqual(a["record_id"], b["record_id"])

    def test_grade_sorting(self):
        self.assertLess(grade_key("V4+"), grade_key("V5-"))
        self.assertEqual(grade_key("V6"), (6, 0))

    def test_analytics_counts_sends_and_flashes(self):
        rows = [
            normalize({"board":"kilter", "date":"2026-11-02 10:00:00", "climb_name":"A", "displayed_grade":"V5", "tries":"1", "is_ascent":"True", "angle":"40"}),
            normalize({"board":"kilter", "date":"2026-11-02 10:05:00", "climb_name":"B", "displayed_grade":"V4", "tries":"3", "is_ascent":"True", "angle":"40"}),
            normalize({"board":"tension", "date":"2026-11-03 10:00:00", "climb_name":"C", "displayed_grade":"V3", "tries":"2", "is_ascent":"False", "angle":"35"}),
        ]
        result = analytics(rows)
        self.assertEqual(result["Overview"][2][1:], [2, 2, 0])
        self.assertEqual(result["Overview"][6][1:], [1, 1, 0])
        self.assertEqual(result["Grade Pyramid"][1][1], 1)

    def test_legacy_sheet_migration_with_header(self):
        rows = existing_records([["date", "route_name", "grade"], ["2025-01-01", "Old climb", "V3"]])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["board"], "legacy")
        self.assertEqual(rows[0]["climb_name"], "Old climb")
        self.assertEqual(rows[0]["displayed_grade"], "V3")

    def test_legacy_sheet_migration_without_header(self):
        rows = existing_records([["2025-01-01", "First old climb", "V2"], ["2025-01-02", "Second old climb", "V3"]])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["climb_name"], "First old climb")
        self.assertEqual(rows[1]["displayed_grade"], "V3")

if __name__ == "__main__":
    unittest.main()
