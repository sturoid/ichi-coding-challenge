"""Check 1 through run(): the README's worked building and the fixture building.

Expected values: README "Check 1" section and PLAN section 2 / Check 1.
"""
import unittest

from ichi.pipeline import run

from helpers import (CNE, CODE_ANALYSIS_HTML, FAIL, PASS, SCHEDULE_HTML, code_analysis_html,
                     readme_building, simple_schedule, swap_tr_blocks, TABLE_HTML)

# Any schedule will do for Check 1; keep it tiny and non-residential.
EMPTY_SCHEDULE = simple_schedule(["SYMBOL", "LOCATION", "WIDTH", "HEIGHT", "TYPE", "HEAD HEIGHT", "EGRESS"],
                                 [["1", "LOBBY 100", "3'-0\"", "4'-0\"", "FIXED", "7'-0\"", ""]])


def height(ca_html, schedule=EMPTY_SCHEDULE, table=None):
    return run(ca_html, schedule, table).by_id()["H1"]


class TestReadmeBuilding(unittest.TestCase):
    """B / II-B / NONE: row 'A, B, E, F, M, S, U', sub-row NS, column II-B = 55."""

    def test_52ft_passes(self):
        h = height(readme_building(height="52'-0\""))
        self.assertEqual(h.verdict, PASS, h.reason)
        self.assertIn("A, B, E, F, M, S, U", h.code_ref)
        self.assertIn("NS", h.code_ref)
        self.assertIn("II-B", h.code_ref)
        text = h.reason + " ".join(h.derivation) + " ".join(e.parsed for e in h.evidence)
        self.assertIn("55", text)

    def test_56ft_fails_by_a_foot(self):
        h = height(readme_building(height="56'-0\""))
        self.assertEqual(h.verdict, FAIL, h.reason)
        self.assertIn("55", h.reason + " ".join(h.derivation))
        text = (h.reason + " " + " ".join(h.derivation) + " " + (h.margin or "")).replace("’", "'")
        self.assertTrue("1'" in text or "1 ft" in text or "12 in" in text or "12.0 in" in text,
                        f"expected a one-foot margin somewhere in: {text}")

    def test_exactly_55_passes(self):
        # "shall not exceed": 55'-0" is allowed.
        self.assertEqual(height(readme_building(height="55'-0\"")).verdict, PASS)

    def test_55ft_1in_fails(self):
        self.assertEqual(height(readme_building(height="55'-1\"")).verdict, FAIL)

    def test_missing_construction_type_is_cne(self):
        h = height(readme_building(construction=None))
        self.assertEqual(h.verdict, CNE, h.reason)

    def test_missing_occupancy_is_cne(self):
        self.assertEqual(height(readme_building(occupancy=None)).verdict, CNE)

    def test_missing_height_is_cne(self):
        self.assertEqual(height(readme_building(height=None)).verdict, CNE)

    def test_missing_sprinkler_line_is_cne_not_guessed(self):
        # No sprinkler line at all: NS and S differ (55 vs 75), so the tool can't pick a sub-row.
        h = height(readme_building(sprinklers=None))
        self.assertEqual(h.verdict, CNE, h.reason)

    def test_sprinklered_nfpa13_uses_S_row(self):
        # B / II-B / NFPA 13 / 70' -> S sub-row = 75: Pass (NS would have failed at 55).
        h = height(readme_building(sprinklers="YES - NFPA 13 (903.3.1.1)", height="70'-0\""))
        self.assertEqual(h.verdict, PASS, h.reason)
        self.assertIn("/ S ", h.code_ref.replace("sub-row ", "/ ") + " ")

    def test_unlimited_cell_passes(self):
        # B / I-A / NS = UL.
        h = height(readme_building(construction="I-A", height="300'-0\""))
        self.assertEqual(h.verdict, PASS, h.reason)

    def test_numbered_group_goes_to_letter_row(self):
        # README: "A numbered group like R-3 goes in the Table 504.3 row for its letter"
        # B-2 is not a real IBC group, so use A-2 (assembly): A-2 / NS / II-B -> 55.
        h = height(readme_building(occupancy="A-2", height="56'-0\""))
        self.assertEqual(h.verdict, FAIL)
        self.assertIn("A, B, E, F, M, S, U", h.code_ref)

    def test_I2_goes_to_its_own_merged_row(self):
        # I-2 / S / II-B: row "I-1 Condition 2, I-2", merged cell = 55. 60' fails.
        h = height(readme_building(occupancy="I-2", sprinklers="YES - NFPA 13 (903.3.1.1)", height="60'-0\""))
        self.assertEqual(h.verdict, FAIL, h.reason)
        self.assertIn("I-1 Condition 2, I-2", h.code_ref)

    def test_H4_is_not_H1(self):
        # H-4 / S / II-B = 75, while H-1 group / S / II-B = 55. 70' passes only in the H-4 row.
        h = height(readme_building(occupancy="H-4", sprinklers="YES - NFPA 13 (903.3.1.1)", height="70'-0\""))
        self.assertEqual(h.verdict, PASS, h.reason)
        self.assertIn("'H-4'", h.code_ref.replace("‘", "'").replace("’", "'"))

    def test_H1_merged_S_row(self):
        h = height(readme_building(occupancy="H-1", sprinklers="YES - NFPA 13 (903.3.1.1)", height="70'-0\""))
        self.assertEqual(h.verdict, FAIL, h.reason)
        self.assertIn("H-1, H-2, H-3, H-5", h.code_ref)


class TestFixtureBuilding(unittest.TestCase):
    """R-3 / V-B / NFPA 13D / 41'-6": row R, sub-row S13D, column V-B = 40 ft. Over by 1'-6"."""

    @classmethod
    def setUpClass(cls):
        cls.result = run(CODE_ANALYSIS_HTML, SCHEDULE_HTML)
        cls.h = cls.result.by_id()["H1"]

    def test_fails(self):
        self.assertEqual(self.h.verdict, FAIL, self.h.reason)

    def test_cell_trace(self):
        ref = self.h.code_ref
        self.assertIn("Table 504.3", ref)
        self.assertIn("'R'", ref.replace("‘", "'").replace("’", "'"))
        self.assertIn("S13D", ref)
        self.assertIn("V-B", ref)
        self.assertNotIn("S13R", ref)

    def test_values_in_evidence(self):
        text = self.h.reason + " " + " ".join(self.h.derivation) + " " + " ".join(e.parsed + e.raw for e in self.h.evidence)
        self.assertIn("40", text)
        self.assertIn("41", text)
        margin = (self.h.margin or "") + " " + self.h.reason + " ".join(self.h.derivation)
        self.assertTrue("1'-6\"" in margin or "1' - 6\"" in margin or "18 in" in margin or "18.0 in" in margin or "1.5 ft" in margin,
                        f"expected the 1'-6\" overage somewhere in: {margin}")

    def test_architect_allowable_height_flagged(self):
        flags = " ".join(self.h.flags)
        self.assertIn("60", flags)
        self.assertIn("40", flags)

    def test_sprinkler_standard_read_as_13D(self):
        text = " ".join(e.parsed for e in self.h.evidence)
        self.assertIn("S13D", text)

    def test_subrow_reorder_does_not_change_verdict(self):
        html = swap_tr_blocks(TABLE_HTML, ">S13D<", ">S13R<")
        h = run(CODE_ANALYSIS_HTML, SCHEDULE_HTML, html).by_id()["H1"]
        self.assertEqual(h.verdict, FAIL)
        self.assertIn("S13D", h.code_ref)
        self.assertEqual(h.code_ref, self.h.code_ref)


class TestSprinklerConflicts(unittest.TestCase):
    def test_13R_citation_gives_60(self):
        ca = code_analysis_html([
            ("OCCUPANCY GROUP", "R-3"), ("CONSTRUCTION TYPE", "V-B"),
            ("FIRE SPRINKLERS", "YES - NFPA 13R (IBC 903.3.1.2)"), ("BUILDING HEIGHT", "41' - 6\""),
        ])
        h = height(ca)
        self.assertEqual(h.verdict, PASS, h.reason)
        self.assertIn("S13R", h.code_ref)

    def test_standard_vs_citation_conflict_is_cne(self):
        # PLAN section 3 values.py: "a conflict with the code citation -> CNE".
        ca = code_analysis_html([
            ("OCCUPANCY GROUP", "R-3"), ("CONSTRUCTION TYPE", "V-B"),
            ("FIRE SPRINKLERS", "YES - NFPA 13D (IBC 903.3.1.2)"), ("BUILDING HEIGHT", "41' - 6\""),
        ])
        h = height(ca)
        self.assertEqual(h.verdict, CNE, h.reason)

    def test_no_sprinklers_spelled_NO(self):
        ca = code_analysis_html([
            ("OCCUPANCY GROUP", "R-3"), ("CONSTRUCTION TYPE", "V-B"),
            ("FIRE SPRINKLERS", "NO"), ("BUILDING HEIGHT", "41' - 6\""),
        ])
        h = height(ca)
        self.assertEqual(h.verdict, FAIL)
        self.assertIn("NS", h.code_ref)


if __name__ == "__main__":
    unittest.main()
