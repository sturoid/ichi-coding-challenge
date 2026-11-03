"""Mutation tests (PLAN section 5): position independence and graceful degradation.

Missing data degrades to Could Not Evaluate, never to a guess (PLAN section 3).
"""
import random
import unittest

from ichi.pipeline import run

from helpers import (CNE, CODE_ANALYSIS_HTML, FAIL, NA, PASS, SCHEDULE_HTML, fixture_columns,
                     schedule_html)


def verdict_map(result):
    return {f.id: (f.verdict, f.reason_code, f.tag) for f in result.findings}


def blocks(columns):
    """Group adjacent columns that share a non-empty top header, so a shuffle keeps
    NOMINAL SIZE / WIDTH, HEIGHT together."""
    out, i = [], 0
    while i < len(columns):
        j = i
        if columns[i][1] is not None and columns[i][0]:
            while j + 1 < len(columns) and columns[j + 1][0] == columns[i][0] and columns[j + 1][1] is not None:
                j += 1
        out.append(columns[i:j + 1])
        i = j + 1
    return out


class TestRebuiltFixtureMatches(unittest.TestCase):
    """Sanity: the hand-transcribed schedule in helpers gives the same verdicts as the file."""

    def test_same_verdicts(self):
        base = verdict_map(run(CODE_ANALYSIS_HTML, SCHEDULE_HTML))
        rebuilt = verdict_map(run(CODE_ANALYSIS_HTML, schedule_html(fixture_columns())))
        self.assertEqual(rebuilt, base)


class TestColumnShuffle(unittest.TestCase):
    def test_shuffled_columns_same_verdicts(self):
        base = verdict_map(run(CODE_ANALYSIS_HTML, SCHEDULE_HTML))
        rng = random.Random(504)
        for trial in range(6):
            bl = blocks(fixture_columns())
            rng.shuffle(bl)
            cols = [c for b in bl for c in b]
            with self.subTest(trial=trial, order=[c[0] or c[1] for c in cols]):
                got = verdict_map(run(CODE_ANALYSIS_HTML, schedule_html(cols)))
                self.assertEqual(got, base)

    def test_reversed_blocks(self):
        base = verdict_map(run(CODE_ANALYSIS_HTML, SCHEDULE_HTML))
        cols = [c for b in reversed(blocks(fixture_columns())) for c in b]
        self.assertEqual(verdict_map(run(CODE_ANALYSIS_HTML, schedule_html(cols))), base)

    def test_type_columns_swapped(self):
        # Mark letters first, operation words second: content, not position, must decide.
        cols = fixture_columns()
        cols[4], cols[5] = cols[5], cols[4]
        base = verdict_map(run(CODE_ANALYSIS_HTML, SCHEDULE_HTML))
        self.assertEqual(verdict_map(run(CODE_ANALYSIS_HTML, schedule_html(cols))), base)

    def test_renamed_headers(self):
        cols = fixture_columns()
        renames = {"SYMBOL": "MK", "LOCATION": "ROOM", "HEAD HEIGHT": "HEAD HT.", "EGRESS": "EGRESS?"}
        cols = [(renames.get(top, top), sub, vals) for top, sub, vals in cols]
        cols = [(top, "W" if sub == "WIDTH" else "H" if sub == "HEIGHT" else sub, vals) for top, sub, vals in cols]
        base = verdict_map(run(CODE_ANALYSIS_HTML, SCHEDULE_HTML))
        self.assertEqual(verdict_map(run(CODE_ANALYSIS_HTML, schedule_html(cols))), base)


class TestDropEgressColumn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cols = [c for c in fixture_columns() if c[0] != "EGRESS"]
        cls.result = run(CODE_ANALYSIS_HTML, schedule_html(cols))
        cls.by_id = cls.result.by_id()

    def test_no_pass_or_fail_by_guess(self):
        for f in self.result.findings:
            if f.check in ("egress-window", "egress-room"):
                with self.subTest(f.id):
                    self.assertNotIn(f.verdict, (PASS, FAIL), f"{f.id}: {f.reason}")

    def test_every_sleeping_room_is_cne(self):
        for rid in ("R101", "R107", "R203", "R205", "R301", "R303"):
            with self.subTest(rid):
                self.assertEqual(self.by_id[rid].verdict, CNE)
                self.assertEqual(self.by_id[rid].reason_code, "NO_EGRESS_COLUMN")

    def test_bedroom_windows_are_cne_not_na(self):
        # Without the column, no window can be ruled out as "not designated".
        for wid in ("W1", "W3", "W7", "W10", "W12", "W13", "W20", "W21"):
            with self.subTest(wid):
                self.assertEqual(self.by_id[wid].verdict, CNE, self.by_id[wid].reason)

    def test_non_sleeping_rooms_still_na(self):
        for wid in ("W5", "W6", "W8", "W14", "W22", "W23"):
            self.assertEqual(self.by_id[wid].verdict, NA)

    def test_observation_logged(self):
        self.assertTrue(any("EGRESS" in o for o in self.result.notes.observations), self.result.notes.observations)

    def test_nothing_disappears(self):
        self.assertEqual({f.id for f in self.result.findings if f.check == "egress-window"},
                         {f"W{s}" for s in (1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 20, 21, 22, 23)})


class TestDropOperationColumn(unittest.TestCase):
    """No operation column: the opening fraction is unknown, so nothing can be shown to open.
    PLAN section 2 still allows a Fail where the window fails under the most favorable reading
    (W10's 5.0 sf nominal area, W20's 60" sill), but anything that leaned on 'casement opens
    fully' or 'fixed does not open' must drop to CNE."""

    @classmethod
    def setUpClass(cls):
        cols = fixture_columns()
        del cols[4]  # the operation TYPE column (L.H. CASM'T / FIXED / ...)
        cls.result = run(CODE_ANALYSIS_HTML, schedule_html(cols))
        cls.by_id = cls.result.by_id()

    def test_no_pass(self):
        self.assertEqual([f.id for f in self.result.findings if f.verdict == PASS and f.id != "H1"], [])

    def test_designated_windows_cne(self):
        for wid in ("W1", "W3", "W7", "W12", "W13"):
            with self.subTest(wid):
                self.assertEqual(self.by_id[wid].verdict, CNE, self.by_id[wid].reason)

    def test_fixed_designated_no_longer_fails(self):
        self.assertNotEqual(self.by_id["W13"].verdict, FAIL)

    def test_undesignated_still_na(self):
        for wid in ("W2", "W5", "W11", "W22"):
            self.assertEqual(self.by_id[wid].verdict, NA)

    def test_fails_where_operation_cannot_help(self):
        # Every operation factor is <= 1, so the nominal area is an upper bound whatever the type:
        # W10's 5.0 sf nominal < 5.7 (floor 2) fails 1030.2 and its 50" sill fails 1030.3; W20's 60"
        # sill fails 1030.3. PLAN section 2: Fail when it fails under the most favorable reading.
        for wid in ("W10", "W20"):
            with self.subTest(wid):
                self.assertEqual(self.by_id[wid].verdict, FAIL, self.by_id[wid].reason)

    def test_observation_logged(self):
        self.assertTrue(any("OPERATION" in o for o in self.result.notes.observations), self.result.notes.observations)


class TestDropOtherColumns(unittest.TestCase):
    def test_drop_head_height(self):
        cols = [c for c in fixture_columns() if c[0] != "HEAD HEIGHT"]
        by_id = run(CODE_ANALYSIS_HTML, schedule_html(cols)).by_id()
        # Sill findings go away: W20 (sill-only Fail) and W7 (sill at limit) become CNE.
        self.assertEqual(by_id["W20"].verdict, CNE, by_id["W20"].reason)
        self.assertEqual(by_id["W7"].verdict, CNE)
        self.assertNotEqual(by_id["W7"].reason_code, "SILL_AT_LIMIT")
        # Area/operation Fails survive without a head height.
        self.assertEqual(by_id["W10"].verdict, FAIL)
        self.assertEqual(by_id["W13"].verdict, FAIL)

    def test_drop_width(self):
        cols = [c for c in fixture_columns() if c[1] != "WIDTH"]
        r = run(CODE_ANALYSIS_HTML, schedule_html(cols))
        by_id = r.by_id()
        for wid in ("W1", "W7", "W12"):
            self.assertEqual(by_id[wid].verdict, CNE, f"{wid}: {by_id[wid].reason}")
        self.assertEqual(by_id["W13"].verdict, FAIL)   # fixed alone decides
        self.assertEqual([f.id for f in r.findings if f.verdict == PASS and f.id != "H1"], [])
        self.assertTrue(any("WIDTH" in o for o in r.notes.observations))

    def test_drop_width_keeps_sill_fail(self):
        # Sill = head - nominal height needs no width. W20's 60" sill and W10's 50" sill fail
        # 1030.3 under any reading (PLAN section 2), so losing the WIDTH column should not
        # soften them to CNE.
        cols = [c for c in fixture_columns() if c[1] != "WIDTH"]
        by_id = run(CODE_ANALYSIS_HTML, schedule_html(cols)).by_id()
        for wid in ("W20", "W10"):
            with self.subTest(wid):
                self.assertEqual(by_id[wid].verdict, FAIL, by_id[wid].reason)
                self.assertIn("1030.3", by_id[wid].code_ref)

    def test_drop_location_column_nothing_passes_or_fails(self):
        cols = [c for c in fixture_columns() if c[0] != "LOCATION"]
        r = run(CODE_ANALYSIS_HTML, schedule_html(cols))
        for f in r.findings:
            if f.check != "height":
                self.assertNotEqual(f.verdict, PASS)
        self.assertEqual(len([f for f in r.findings if f.check == "egress-window"]), 17)


class TestNetClearColumn(unittest.TestCase):
    """A schedule that does give net clear sizes lets windows Pass; a size column whose
    header does not say which size it is must not be taken as net clear (PLAN: COLUMN_AMBIGUOUS)."""

    def _with_net_clear(self, width_header, height_header):
        cols = fixture_columns()
        n = len(cols[0][2])
        cols.insert(4, ("NET CLEAR", width_header, ["2'-2\""] * n))
        cols.insert(5, ("NET CLEAR", height_header, ["3'-8\""] * n))
        cols.insert(6, ("SILL HEIGHT", None, ["2'-8\""] * n))
        return run(CODE_ANALYSIS_HTML, schedule_html(cols))

    def _assert_net_clear_used(self, r):
        by_id = r.by_id()
        self.assertEqual(r.notes.not_read, [], r.notes.not_read)
        # 26 x 44 = 1144 sq in = 7.94 sf >= 5.7; 26 >= 20; 44 >= 24; sill 32 <= 44.
        self.assertEqual(by_id["W1"].verdict, PASS, by_id["W1"].reason)
        self.assertEqual(by_id["R101"].verdict, PASS, by_id["R101"].reason)
        # Still fixed: a fixed unit does not open whatever its glass size.
        self.assertEqual(by_id["W13"].verdict, FAIL)
        # Nominal verdicts (W10 5.0 sf) must defer to the given net clear figures.
        self.assertEqual(by_id["W10"].verdict, PASS, by_id["W10"].reason)

    def test_net_clear_columns_allow_pass(self):
        # Header spellings that can't be confused: W / HT.
        self._assert_net_clear_used(self._with_net_clear("W", "HT"))

    def test_net_clear_width_height_spelling(self):
        # The obvious spelling: NET CLEAR / WIDTH and NET CLEAR / HEIGHT. "WIDTH" ends in H, which
        # must not make it look like a height column.
        r = self._with_net_clear("WIDTH", "HEIGHT")
        self.assertEqual([h for h, field, how in r.notes.header_map if h == "NET CLEAR / WIDTH"], ["NET CLEAR / WIDTH"])
        mapped = {h: field for h, field, how in r.notes.header_map}
        self.assertEqual(mapped["NET CLEAR / WIDTH"], "net_clear_width", r.notes.not_read)
        self._assert_net_clear_used(r)

    def test_rough_opening_is_not_net_clear(self):
        cols = fixture_columns()
        n = len(cols[0][2])
        cols.insert(4, ("ROUGH OPENING", "W", ["2'-8\""] * n))
        cols.insert(5, ("ROUGH OPENING", "H", ["4'-2\""] * n))
        by_id = run(CODE_ANALYSIS_HTML, schedule_html(cols)).by_id()
        self.assertEqual(by_id["W1"].verdict, CNE, by_id["W1"].reason)
        self.assertEqual(by_id["W10"].verdict, FAIL)

    def test_bare_size_columns_are_not_net_clear(self):
        cols = fixture_columns()
        cols = [("SIZE" if top == "NOMINAL SIZE" else top, sub, vals) for top, sub, vals in cols]
        r = run(CODE_ANALYSIS_HTML, schedule_html(cols))
        by_id = r.by_id()
        self.assertNotEqual(by_id["W1"].verdict, PASS)
        self.assertNotEqual(by_id["W7"].verdict, PASS)


if __name__ == "__main__":
    unittest.main()
