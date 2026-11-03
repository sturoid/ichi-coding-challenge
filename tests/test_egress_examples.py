"""Check 2 on the README's worked examples (W-A, W-B, Bedroom 2) and small variants whose
answers follow directly from the text of Section 1030.

- 1030.2: net clear >= 5.7 sf (5.0 for a grade-floor opening)
- 1030.2.1: net clear height >= 24 in, width >= 20 in, "result of normal operation"
- 1030.3: bottom of clear opening <= 44 in from floor
- 1030.1.1: operational from inside without keys or tools

PLAN section 2: Fail only under the most favorable reading. A room whose floor is unknown
(README "BEDROOM 2", no numbering) might hold a grade-floor opening, so the favorable area
floor is 5.0 sf; a window that beats 5.0 but not 5.7 at nominal is CNE, not Fail.

Findings are located by position and room rather than id because the README's symbols
("W-A") are not read as symbols by the current mapper (see TestSymbolColumn).
"""
import unittest

from ichi.pipeline import run

from helpers import (CNE, FAIL, NA, PASS, R3_CODE_ANALYSIS, README_WINDOW_HEADERS, W_A, W_B,
                     code_analysis_html, simple_schedule, the_room, windows_of)


def check(rows, ca=R3_CODE_ANALYSIS, headers=README_WINDOW_HEADERS):
    return run(ca, simple_schedule(headers, rows))


def one(rows, **kw):
    """The single window finding of a one-row schedule."""
    ws = windows_of(check(rows, **kw))
    assert len(ws) == 1, [w.id for w in ws]
    return ws[0]


def win(symbol, location, w, h, op, head, egress="Y"):
    return [symbol, location, w, h, op, head, egress]


class TestSymbolColumn(unittest.TestCase):
    """The README's own worked example uses symbols 'W-A' and 'W-B'. The schedule's SYMBOL column
    must be read whatever the symbol style, so findings keep the drawing's window ids."""

    def test_readme_symbols_are_read(self):
        r = check([W_A, W_B])
        ids = {f.id for f in r.findings}
        self.assertIn("WW-A", ids, f"SYMBOL column not read: {sorted(ids)}; not read: {r.notes.not_read}")
        self.assertIn("WW-B", ids)
        self.assertEqual(r.notes.not_read, [])

    def test_numeric_symbols_are_read(self):
        r = check([win("7", "BEDROOM 2", "2'-0\"", "2'-0\"", "CASEMENT", "6'-8\"")])
        self.assertIn("W7", {f.id for f in r.findings})

    def test_alphanumeric_symbols_are_read(self):
        r = check([win("101A", "BEDROOM 2", "2'-0\"", "2'-0\"", "CASEMENT", "6'-8\"")])
        self.assertIn("W101A", {f.id for f in r.findings}, [f.id for f in r.findings])


class TestReadmeWindows(unittest.TestCase):
    def test_WA_2x2_casement_fails(self):
        f = one([W_A])
        self.assertEqual(f.verdict, FAIL, f.reason)
        self.assertIn("1030.2", f.code_ref)
        text = f.reason + " ".join(f.derivation)
        self.assertIn("4.0", text)

    def test_WB_3x3_6_casement_is_cne(self):
        f = one([W_B])
        self.assertEqual(f.verdict, CNE, f.reason)
        text = (f.reason + " " + " ".join(f.derivation) + " " + " ".join(f.assumptions)).lower()
        self.assertIn("net clear", text)
        # README: the sill is derived (7'-0" - 3'-6" = 3'-6" = 42"), and the report must say so.
        self.assertTrue("42" in text or "3'-6\"" in text or "3' - 6\"" in text, text)
        self.assertTrue(f.settles_with, "a CNE must say what settles it")
        self.assertNotEqual(f.tag, "boundary", "10.5 sf nominal vs 5.7 is nowhere near the limit")

    def test_bedroom_2_is_cne(self):
        r = check([W_A, W_B])
        wa, wb = windows_of(r)
        self.assertEqual(wa.verdict, FAIL)
        self.assertEqual(wb.verdict, CNE)
        room = the_room(r)
        self.assertEqual(room.verdict, CNE, room.reason)
        self.assertEqual(room.room, "BEDROOM 2")
        self.assertEqual(len(room.windows), 2, room.windows)

    def test_bedroom_with_only_WA_fails(self):
        room = the_room(check([W_A]))
        self.assertEqual(room.verdict, FAIL, room.reason)
        self.assertIn("1030.1", room.code_ref)

    def test_WB_alone_room_is_cne(self):
        self.assertEqual(the_room(check([W_B])).verdict, CNE)


class TestOperationBounds(unittest.TestCase):
    """Window type caps the fraction of the nominal unit that can open (README: a single hung
    only opens its bottom half, a fixed window doesn't open). PLAN section 2: the factor applies
    to area as well as height."""

    def test_fixed_designated_fails_operation(self):
        f = one([win("1", "BEDROOM 2", "4'-0\"", "4'-0\"", "FIXED", "6'-8\"")])
        self.assertEqual(f.verdict, FAIL, f.reason)
        self.assertTrue("1030.1.1" in f.code_ref or "1030.2.1" in f.code_ref, f.code_ref)

    def test_single_hung_under_48_fails_height(self):
        # S.H. 3'-0" x 3'-10": operable height at best 23" < 24" (1030.2.1), even with zero frame.
        f = one([win("1", "BEDROOM 2", "3'-0\"", "3'-10\"", "S.H.", "6'-8\"")])
        self.assertEqual(f.verdict, FAIL, f.reason)
        self.assertIn("1030.2.1", f.code_ref)

    def test_single_hung_exactly_48_is_boundary_cne(self):
        f = one([win("1", "BEDROOM 2", "3'-0\"", "4'-0\"", "S.H.", "6'-8\"")])
        self.assertEqual(f.verdict, CNE, f.reason)
        self.assertEqual(f.tag, "boundary")
        self.assertEqual(f.reason_code, "HUNG_HEIGHT_AT_LIMIT")

    def test_single_hung_small_area_fails(self):
        # S.H. 2'-0" x 4'-6": half height 27" is fine, but half of 9 sf = 4.5 sf < 5.0 even as a
        # grade-floor opening.
        f = one([win("1", "BEDROOM 2", "2'-0\"", "4'-6\"", "S.H.", "7'-0\"")])
        self.assertEqual(f.verdict, FAIL, f.reason)
        self.assertIn("1030.2", f.code_ref)

    def test_single_hung_between_5_and_5_7_on_unknown_floor_is_cne(self):
        # S.H. 2'-0" x 5'-0": half of 10 sf = 5.0 sf, enough only for a grade-floor opening.
        f = one([win("1", "BEDROOM 2", "2'-0\"", "5'-0\"", "S.H.", "7'-0\"")])
        self.assertEqual(f.verdict, CNE, f.reason)
        self.assertIn("grade", (f.reason + " ".join(f.derivation)).lower())

    def test_single_hung_between_5_and_5_7_on_upper_floor_fails(self):
        ca = code_analysis_html([("OCCUPANCY GROUP", "R-3"), ("CONSTRUCTION TYPE", "V-B"),
                                 ("SPRINKLERS", "NONE"), ("BUILDING HEIGHT", "30'-0\""),
                                 ("ROOM NUMBERING", "1XX = FIRST FLOOR, 2XX = SECOND FLOOR")])
        f = one([win("1", "BEDROOM 201", "2'-0\"", "5'-0\"", "S.H.", "7'-0\"")], ca=ca)
        self.assertEqual(f.verdict, FAIL, f.reason)

    def test_slider_half_width_fails_width(self):
        # Slider 3'-0" x 4'-0": operable width at best 18" < 20" (1030.2.1).
        f = one([win("1", "BEDROOM 2", "3'-0\"", "4'-0\"", "SLIDER", "6'-8\"")])
        self.assertEqual(f.verdict, FAIL, f.reason)
        self.assertIn("1030.2.1", f.code_ref)

    def test_big_slider_is_cne(self):
        # Slider 6'-0" x 4'-0": half width 36", half area 12 sf -> can't be decided from nominal.
        f = one([win("1", "BEDROOM 2", "6'-0\"", "4'-0\"", "SLIDER", "6'-8\"")])
        self.assertEqual(f.verdict, CNE, f.reason)

    def test_casement_narrow_fails_width(self):
        # Casement 1'-6" x 5'-0": nominal width 18" < 20" (1030.2.1); area 7.5 sf is fine.
        f = one([win("1", "BEDROOM 2", "1'-6\"", "5'-0\"", "CASEMENT", "7'-0\"")])
        self.assertEqual(f.verdict, FAIL, f.reason)
        self.assertIn("1030.2.1", f.code_ref)

    def test_casement_short_fails_height(self):
        # Casement 4'-0" x 1'-10": nominal height 22" < 24".
        f = one([win("1", "BEDROOM 2", "4'-0\"", "1'-10\"", "CASEMENT", "6'-8\"")])
        self.assertEqual(f.verdict, FAIL, f.reason)

    def test_unknown_operation_word_is_cne(self):
        f = one([win("1", "BEDROOM 2", "3'-0\"", "4'-0\"", "TILT-TURN", "6'-8\"")])
        self.assertEqual(f.verdict, CNE, f.reason)

    def test_blank_operation_is_cne(self):
        f = one([win("1", "BEDROOM 2", "3'-0\"", "4'-0\"", "", "6'-8\"")])
        self.assertEqual(f.verdict, CNE, f.reason)


class TestSill(unittest.TestCase):
    def test_sill_over_44_fails(self):
        # 8'-0" head - 3'-0" unit = 60" sill > 44" (1030.3), under any datum.
        f = one([win("1", "BEDROOM 2", "2'-6\"", "3'-0\"", "CASEMENT", "8'-0\"")])
        self.assertEqual(f.verdict, FAIL, f.reason)
        self.assertIn("1030.3", f.code_ref)

    def test_sill_exactly_44_is_boundary_cne(self):
        # 6'-8" - 3'-0" = 44.0": the limit itself; any frame pushes the clear opening above it.
        f = one([win("1", "BEDROOM 2", "2'-6\"", "3'-0\"", "CASEMENT", "6'-8\"")])
        self.assertEqual(f.verdict, CNE, f.reason)
        self.assertEqual(f.tag, "boundary")
        self.assertEqual(f.reason_code, "SILL_AT_LIMIT")

    def test_no_head_height_column_is_cne_not_fail(self):
        headers = ["SYMBOL", "LOCATION", "WIDTH", "HEIGHT", "TYPE", "EGRESS"]
        f = one([["1", "BEDROOM 2", "3'-0\"", "4'-0\"", "CASEMENT", "Y"]], headers=headers)
        self.assertEqual(f.verdict, CNE, f.reason)

    def test_small_window_fails_even_without_head_height(self):
        headers = ["SYMBOL", "LOCATION", "WIDTH", "HEIGHT", "TYPE", "EGRESS"]
        f = one([["1", "BEDROOM 2", "2'-0\"", "2'-0\"", "CASEMENT", "Y"]], headers=headers)
        self.assertEqual(f.verdict, FAIL, f.reason)

    def test_sill_column_is_used_directly(self):
        headers = ["SYMBOL", "LOCATION", "WIDTH", "HEIGHT", "TYPE", "SILL HEIGHT", "EGRESS"]
        f = one([["1", "BEDROOM 2", "2'-6\"", "3'-0\"", "CASEMENT", "4'-0\"", "Y"]], headers=headers)
        self.assertEqual(f.verdict, FAIL, f.reason)
        self.assertIn("1030.3", f.code_ref)


class TestApplicability(unittest.TestCase):
    def test_non_sleeping_room_is_na(self):
        r = check([win("1", "KITCHEN 104", "3'-0\"", "3'-0\"", "AWNING", "7'-0\"", "")])
        self.assertEqual(windows_of(r)[0].verdict, NA)
        self.assertEqual([f for f in r.findings if f.check == "egress-room"], [])

    def test_den_is_ambiguous_not_guessed(self):
        r = check([win("1", "DEN 102", "3'-0\"", "5'-0\"", "CASEMENT", "7'-0\"", "")])
        room = the_room(r)
        self.assertEqual(room.verdict, CNE)
        self.assertEqual(room.reason_code, "AMBIGUOUS_SLEEPING_ROOM")
        self.assertNotIn(windows_of(r)[0].verdict, (PASS, FAIL))

    def test_bedroom_spellings(self):
        for name in ("BDRM 5", "BED 5", "MASTER BEDROOM 5", "GUEST BED 5", "MSTR BDRM 5", "Bedroom 5", "BEDRROM 5"):
            with self.subTest(name=name):
                r = check([win("1", name, "2'-0\"", "2'-0\"", "CASEMENT", "6'-8\"")])
                self.assertEqual(windows_of(r)[0].verdict, FAIL)
                self.assertEqual(the_room(r).verdict, FAIL)

    def test_bedroom_without_designated_window_is_cne(self):
        room = the_room(check([win("1", "BEDROOM 2", "3'-0\"", "4'-0\"", "CASEMENT", "6'-8\"", "")]))
        self.assertEqual(room.verdict, CNE)
        self.assertEqual(room.reason_code, "NO_EERO_DESIGNATED")

    def test_office_building_windows_are_na(self):
        # 1030.1 lists R-2 (one exit), R-3 and R-4 only. A Group B building has no EERO duty.
        ca = code_analysis_html([("OCCUPANCY GROUP", "B"), ("CONSTRUCTION TYPE", "II-B"),
                                 ("SPRINKLERS", "NONE"), ("BUILDING HEIGHT", "30'-0\"")])
        f = one([W_A], ca=ca)
        self.assertEqual(f.verdict, NA, f.reason)

    def test_R4_applies(self):
        ca = code_analysis_html([("OCCUPANCY GROUP", "R-4"), ("CONSTRUCTION TYPE", "V-B"),
                                 ("SPRINKLERS", "NONE"), ("BUILDING HEIGHT", "30'-0\"")])
        self.assertEqual(one([W_A], ca=ca).verdict, FAIL)

    def test_R2_without_exit_count_is_cne(self):
        # 1030.1 item 1: R-2 only where a story has one exit (Tables 1006.3.3); neither document
        # shows exit counts, so applicability itself is open: CNE, not Fail and not N/A.
        ca = code_analysis_html([("OCCUPANCY GROUP", "R-2"), ("CONSTRUCTION TYPE", "V-A"),
                                 ("SPRINKLERS", "NONE"), ("BUILDING HEIGHT", "30'-0\"")])
        r = check([W_A], ca=ca)
        f = windows_of(r)[0]
        self.assertEqual(f.verdict, CNE, f.reason)
        self.assertEqual(f.reason_code, "APPLICABILITY_UNCLEAR")
        self.assertIn("1030.1", f.reason + f.code_ref)
        self.assertEqual(the_room(r).verdict, CNE)

    def test_fourth_story_bedroom_is_na(self):
        # 1030.1: sleeping rooms "below the fourth story above grade plane".
        ca = code_analysis_html([("OCCUPANCY GROUP", "R-3"), ("CONSTRUCTION TYPE", "V-B"),
                                 ("SPRINKLERS", "NONE"), ("BUILDING HEIGHT", "45'-0\""),
                                 ("NUMBER OF STORIES", "4"),
                                 ("ROOM NUMBERING", "1XX = FIRST FLOOR, 2XX = SECOND FLOOR, 3XX = THIRD FLOOR, 4XX = FOURTH FLOOR")])
        f = one([win("1", "BEDROOM 401", "2'-0\"", "2'-0\"", "CASEMENT", "6'-8\"")], ca=ca)
        self.assertEqual(f.verdict, NA, f.reason)

    def test_missing_occupancy_does_not_fail_windows(self):
        ca = code_analysis_html([("CONSTRUCTION TYPE", "V-B"), ("BUILDING HEIGHT", "30'-0\"")])
        f = one([W_A], ca=ca)
        self.assertNotIn(f.verdict, (PASS, FAIL), f.reason)


if __name__ == "__main__":
    unittest.main()
