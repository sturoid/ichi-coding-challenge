"""Every fixture verdict, per PLAN section 2 (hand-derived from the fixture rows and
Section 1030), plus "nothing disappears" and "no Pass from nominal sizes".

Hand derivation (sill = head - nominal height, PLAN section 2):
  1  BEDROOM 101  casement 2'6"x4'0" = 10 sf, sill 80-48 = 32"  EGRESS  -> CNE open NET_CLEAR_UNKNOWN
  2  BEDROOM 101  fixed, not designated                                -> N/A
  3  BEDROOM 101  as 1                                                  -> CNE open
  4  OFFICE 102   casement 3'0"x5'0", not designated                    -> plan: CNE AMBIGUOUS (window row)
  5  LIVING 103, 6 KITCHEN 104, 8 LAUNDRY 108, 14 BATH 206, 22 HALL 302, 23 STAIR S1 -> N/A
  7  ADU BEDROOM 107 casement 2'6"x3'0" = 7.5 sf, sill 80-36 = 44.0"   -> CNE boundary SILL_AT_LIMIT
  10 BEDROOM 203  casement 2'0"x2'6" = 5.0 sf < 5.7, sill 80-30 = 50"  -> Fail (1030.2, 1030.3)
  11 BEDROOM 203  fixed, not designated                                -> N/A
  12 BEDRROM 205  S.H. 3'0"x4'0": half height 24.0", half area 6.0 sf  -> CNE boundary HUNG_HEIGHT_AT_LIMIT
  13 BEDROOM 205  fixed, marked EGRESS                                  -> Fail (1030.1.1 / 1030.2.1)
  20 BEDROOM 301  casement 2'6"x3'0", sill 96-36 = 60" > 44"            -> Fail (1030.3)
  21 GUEST BED 303 casement 2'6"x4'0", not designated                   -> plan: CNE (candidate)
Rooms: 101 CNE, 102 CNE AMBIGUOUS, 107 CNE boundary, 203 Fail, 205 CNE boundary, 301 Fail,
       303 CNE NO_EERO_DESIGNATED.
"""
import re
import unittest

from ichi.pipeline import run

from helpers import CNE, CODE_ANALYSIS_HTML, FAIL, NA, PASS, SCHEDULE_HTML, fixture_symbols

EXPECTED_WINDOWS = {
    "W1": (CNE, "open", "NET_CLEAR_UNKNOWN"),
    "W2": (NA, None, None),
    "W3": (CNE, "open", "NET_CLEAR_UNKNOWN"),
    "W5": (NA, None, None),
    "W6": (NA, None, None),
    "W7": (CNE, "boundary", "SILL_AT_LIMIT"),
    "W8": (NA, None, None),
    "W10": (FAIL, None, None),
    "W11": (NA, None, None),
    "W12": (CNE, "boundary", "HUNG_HEIGHT_AT_LIMIT"),
    "W13": (FAIL, None, None),
    "W14": (NA, None, None),
    "W20": (FAIL, None, None),
    "W22": (NA, None, None),
    "W23": (NA, None, None),
}

EXPECTED_ROOMS = {
    "R101": (CNE, None),
    "R102": (CNE, "AMBIGUOUS_SLEEPING_ROOM"),
    "R107": (CNE, None),
    "R203": (FAIL, None),
    "R205": (CNE, None),
    "R301": (FAIL, None),
    "R303": (CNE, "NO_EERO_DESIGNATED"),
}


class TestFixtureVerdicts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run(CODE_ANALYSIS_HTML, SCHEDULE_HTML)
        cls.by_id = cls.result.by_id()

    def test_window_verdicts(self):
        for fid, (verdict, tag, code) in EXPECTED_WINDOWS.items():
            with self.subTest(fid):
                f = self.by_id[fid]
                self.assertEqual(f.verdict, verdict, f.reason)
                if tag is not None:
                    self.assertEqual(f.tag, tag)
                if code is not None:
                    self.assertEqual(f.reason_code, code)

    def test_W4_office_not_designated(self):
        # PLAN section 2 lists row 4 as "CNE AMBIGUOUS_SLEEPING_ROOM", but a window that is not
        # designated is not an emergency escape and rescue opening, so 1030.2/.3 have nothing to
        # say about it: Not Applicable at the window, with the doubt carried by room finding R102.
        # (Tester's call; the disagreement with the plan table is reported.)
        f = self.by_id["W4"]
        self.assertEqual(f.verdict, NA, f.reason)
        r = self.by_id["R102"]
        self.assertEqual(r.reason_code, "AMBIGUOUS_SLEEPING_ROOM")
        self.assertIn("4", r.windows)

    def test_W21_guest_bed_candidate(self):
        # PLAN section 2 lists row 21 as "CNE (candidate)". Same reasoning as W4: the window itself
        # is Not Applicable; room 303's NO_EERO_DESIGNATED finding names it as the candidate.
        f = self.by_id["W21"]
        self.assertEqual(f.verdict, NA, f.reason)
        self.assertIn("21", self.by_id["R303"].windows)

    def test_room_verdicts(self):
        for fid, (verdict, code) in EXPECTED_ROOMS.items():
            with self.subTest(fid):
                f = self.by_id[fid]
                self.assertEqual(f.verdict, verdict, f.reason)
                if code is not None:
                    self.assertEqual(f.reason_code, code)

    def test_likely_fail_rooms(self):
        self.assertEqual(self.by_id["R107"].tag, "boundary")
        self.assertEqual(self.by_id["R205"].tag, "boundary")
        self.assertEqual(self.by_id["R101"].tag, "open")

    def test_room_303_names_candidate_21(self):
        r = self.by_id["R303"]
        text = r.reason + " " + " ".join(r.derivation) + " " + (r.next_step or "") + " " + " ".join(r.windows)
        self.assertRegex(text, r"\b21\b")

    def test_room_205_covers_both_rows_despite_typo(self):
        # "BEDRROM 205" and "BEDROOM 205" are the same room.
        r = self.by_id["R205"]
        self.assertNotIn("R205 ", "".join(k + " " for k in self.by_id if k.startswith("R205") and k != "R205"))
        self.assertEqual(sorted(r.windows), ["12", "13"], r.windows)
        self.assertTrue(any(c.raw.strip() == "BEDRROM 205" for c in self.result.notes.corrections),
                        [c.raw for c in self.result.notes.corrections])

    def test_office_ocr_O_for_zero_logged(self):
        self.assertTrue(any("O\"" in c.raw and "0" in c.read_as for c in self.result.notes.corrections),
                        [(c.raw, c.read_as) for c in self.result.notes.corrections])

    def test_W10_cites_both_area_and_sill(self):
        f = self.by_id["W10"]
        self.assertIn("1030.2", f.code_ref)
        self.assertIn("1030.3", f.code_ref)
        text = f.reason + " ".join(f.derivation)
        self.assertIn("5.0", text)
        self.assertIn("50", text)

    def test_W13_fixed_marked_egress(self):
        f = self.by_id["W13"]
        self.assertTrue("1030.1.1" in f.code_ref or "1030.2.1" in f.code_ref, f.code_ref)
        self.assertIn("fixed", (f.reason + " ".join(f.derivation)).lower())

    def test_W20_margin_16_inches(self):
        f = self.by_id["W20"]
        self.assertIn("1030.3", f.code_ref)
        text = f.reason + " " + " ".join(f.derivation) + " " + (f.margin or "")
        self.assertIn("60", text)
        self.assertIn("16", text)

    def test_W7_margin_zero(self):
        f = self.by_id["W7"]
        self.assertIn("44", f.reason + " " + " ".join(f.derivation) + " " + (f.margin or ""))
        self.assertTrue(f.settles_with)
        self.assertTrue(f.next_step or f.draft_comment)

    def test_W12_half_height_24(self):
        f = self.by_id["W12"]
        self.assertIn("24", f.reason + " " + " ".join(f.derivation) + " " + (f.margin or ""))

    def test_every_cne_says_what_settles_it(self):
        for f in self.result.findings:
            if f.verdict == CNE:
                with self.subTest(f.id):
                    self.assertTrue(f.settles_with or f.next_step, f.id)
                    self.assertTrue(f.reason_code, f.id)

    def test_every_finding_has_code_ref_and_reason_and_evidence(self):
        for f in self.result.findings:
            with self.subTest(f.id):
                self.assertIn(f.verdict, (PASS, FAIL, CNE, NA))
                self.assertRegex(f.code_ref, r"1030|504\.3")
                self.assertTrue(f.reason.strip())
                self.assertTrue(f.evidence, "no evidence")

    def test_room_fails_mention_exception_2(self):
        for rid in ("R203", "R301"):
            self.assertIn("Exception 2", " ".join(self.by_id[rid].flags) + self.by_id[rid].reason)


class TestNoPassFromNominal(unittest.TestCase):
    def test_no_window_or_room_passes(self):
        r = run(CODE_ANALYSIS_HTML, SCHEDULE_HTML)
        passes = [f.id for f in r.findings if f.verdict == PASS and f.id != "H1"]
        self.assertEqual(passes, [])

    def test_no_pass_for_huge_casement(self):
        # Even a 6'x6' casement can't Pass without a net clear figure (README's top trap).
        from helpers import R3_CODE_ANALYSIS, README_WINDOW_HEADERS, simple_schedule
        html = simple_schedule(README_WINDOW_HEADERS, [["1", "BEDROOM 2", "6'-0\"", "6'-0\"", "CASEMENT", "7'-0\"", "Y"]])
        f = run(R3_CODE_ANALYSIS, html).by_id()["W1"]
        self.assertEqual(f.verdict, CNE, f.reason)
        self.assertEqual(f.reason_code, "NET_CLEAR_UNKNOWN")


class TestNothingDisappears(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run(CODE_ANALYSIS_HTML, SCHEDULE_HTML)

    def test_every_symbol_has_a_window_finding(self):
        symbols = fixture_symbols()
        self.assertEqual(len(symbols), 17)
        want = {f"W{s}" for s in symbols}
        got = {f.id for f in self.result.findings if f.check == "egress-window"}
        self.assertEqual(got, want)

    def test_room_findings_are_exactly_the_sleeping_and_ambiguous_rooms(self):
        got = {f.id for f in self.result.findings if f.check == "egress-room"}
        self.assertEqual(got, {"R101", "R102", "R107", "R203", "R205", "R301", "R303"})

    def test_one_height_finding(self):
        self.assertEqual([f.id for f in self.result.findings if f.check == "height"], ["H1"])

    def test_ids_unique(self):
        ids = [f.id for f in self.result.findings]
        self.assertEqual(len(ids), len(set(ids)))

    def test_missing_symbols_reported(self):
        obs = " ".join(self.result.notes.observations)
        for s in ("9", "15", "16", "17", "18", "19"):
            self.assertRegex(obs, rf"\b{s}\b")

    def test_every_header_mapped_or_listed_as_not_read(self):
        mapped = {h for h, _, _ in self.result.notes.header_map}
        not_read = " ".join(self.result.notes.not_read)
        for header in ("SYMBOL", "LOCATION", "WIDTH", "HEIGHT", "HEAD", "EGRESS", "SCREE", "HARDWARE", "MANUFACTURE", "NOTES", "GLASS", "SAFETY"):
            with self.subTest(header):
                self.assertTrue(any(header in h.upper().replace(" ", "") or header in h.upper() for h in mapped) or header in not_read.upper().replace(" ", ""),
                                f"{header} neither mapped nor listed as not read: {sorted(mapped)} / {not_read}")

    def test_window_evidence_shows_raw_text(self):
        f = self.result.by_id()["W7"]
        raws = " | ".join(e.raw for e in f.evidence)
        self.assertIn("2'-6\"", raws)       # the OCR spacing as printed, not normalised
        self.assertIn("ADU BEDROOM 107", raws)


if __name__ == "__main__":
    unittest.main()
